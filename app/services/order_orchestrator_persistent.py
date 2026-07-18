from typing import Dict, Any, List
from sqlalchemy.orm import Session
import asyncio

from app.services.workflow_manager_persistent import WorkflowManagerPersistent
from app.services.event_publisher import EventPublisher
from app.services.websocket_publisher import WebSocketPublisher
from app.workflow.runner import get_workflow_runner
from app.domain.enums import OrderState, EventType
from app.core.exceptions import OrderNotFoundError, InvalidStateError


class OrderOrchestratorPersistent:
    """Versão persistente do OrderOrchestrator com notificações via WebSocket."""

    def __init__(self, db: Session):
        self.db = db
        self.event_publisher = EventPublisher()
        self.workflow_manager = WorkflowManagerPersistent(db, self.event_publisher)
        self.workflow_runner = get_workflow_runner()

    def create_order(self, session_id: str, message: str) -> Dict[str, Any]:
        order = self.workflow_manager.create_order(session_id, message)
        runner_result = self.workflow_runner.start(order.id, session_id, message)

        if runner_result["status"] == "interrupted":
            intentions = runner_result.get("intentions", [])
            event = self.event_publisher.create_event(
                order_id=order.id,
                event_type=EventType.INTENTIONS_EXTRACTED.value,
                source="intent_analyzer",
                payload={"intentions": intentions}
            )
            self.event_publisher.publish(event)
            self.workflow_manager.advance_state(order.id, EventType.INTENTIONS_EXTRACTED)

            # 🔥 Notifica via WebSocket que os chips estão prontos
            asyncio.create_task(
                WebSocketPublisher.publish_chips(order.id, intentions)
            )

        return {
            "order_id": order.id,
            "status": runner_result["status"],
            "intentions": runner_result.get("intentions", []),
            "current_step": runner_result.get("current_step", ""),
        }

    def get_order_state(self, order_id: str) -> Dict[str, Any]:
        order = self.workflow_manager.get_order(order_id)
        if not order:
            raise OrderNotFoundError(f"Pedido {order_id} não encontrado")

        chips = self.workflow_manager.get_chips(order_id)
        events = self.workflow_manager.get_events(order_id)

        return {
            "order_id": order_id,
            "status": order.current_state.value,
            "chips": [chip.dict() for chip in chips],
            "events": [event.dict() for event in events],
        }

    def confirm_intentions(self, order_id: str, confirmed_chips: List[Dict[str, Any]]) -> Dict[str, Any]:
        order = self.workflow_manager.get_order(order_id)
        if not order:
            raise OrderNotFoundError(f"Pedido {order_id} não encontrado")

        if order.current_state != OrderState.AGUARDANDO_CONFIRMACAO:
            raise InvalidStateError(
                f"Pedido não está aguardando confirmação. Estado atual: {order.current_state.value}"
            )

        # 🔥 Notifica que o Chef está começando
        asyncio.create_task(
            WebSocketPublisher.publish_step_started(order_id, "chef")
        )

        self.workflow_manager.confirm_intentions(order_id, confirmed_chips)

        runner_result = self.workflow_runner.resume(order_id, confirmed_chips)

        if runner_result["status"] == "completed":
            proposal_content = runner_result.get("proposal")
            if proposal_content:
                # 🔥 Notifica que a receita foi criada
                asyncio.create_task(
                    WebSocketPublisher.publish_step_completed(
                        order_id, 
                        "chef", 
                        {"proposal": proposal_content}
                    )
                )

                # 🔥 Notifica que o Maestro está analisando
                asyncio.create_task(
                    WebSocketPublisher.publish_step_started(order_id, "maestro")
                )

                self.workflow_manager.set_proposal(order_id, proposal_content)
                self.workflow_manager.advance_state(order_id, EventType.ANALYSIS_COMPLETED)
                self.workflow_manager.advance_state(order_id, EventType.NO_CONFLICT)
                self.workflow_manager.finalize_order(order_id, {
                    "result": runner_result.get("result"),
                    "proposal": proposal_content,
                })

                # 🔥 Notifica que a análise foi concluída
                asyncio.create_task(
                    WebSocketPublisher.publish_step_completed(
                        order_id,
                        "maestro",
                        {"analyses": runner_result.get("analyses", [])}
                    )
                )

                # 🔥 Notifica que o resultado final está pronto
                asyncio.create_task(
                    WebSocketPublisher.publish_result(
                        order_id,
                        {
                            "proposal": proposal_content,
                            "result": runner_result.get("result"),
                            "analyses": runner_result.get("analyses", []),
                        }
                    )
                )

        return {
            "order_id": order_id,
            "status": runner_result["status"],
            "result": runner_result.get("result"),
            "proposal": runner_result.get("proposal"),
        }

    def get_result(self, order_id: str) -> Dict[str, Any]:
        order = self.workflow_manager.get_order(order_id)
        if not order:
            raise OrderNotFoundError(f"Pedido {order_id} não encontrado")

        if order.current_state != OrderState.FINALIZADO:
            raise InvalidStateError(f"Pedido ainda não finalizado. Estado: {order.current_state.value}")

        proposal = self.workflow_manager.proposal_repo.get_by_order(order_id)
        proposal_content = proposal.content if proposal else None

        return {
            "order_id": order_id,
            "status": order.current_state.value,
            "proposal": proposal_content,
            "result": proposal_content,
        }