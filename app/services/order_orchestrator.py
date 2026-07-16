from typing import Dict, Any, List, Optional
from app.services.workflow_manager import WorkflowManager
from app.services.event_publisher import EventPublisher
from app.workflow.runner import WorkflowRunner
from app.domain.enums import OrderState, EventType
from app.core.exceptions import OrderNotFoundError, InvalidStateError


class OrderOrchestrator:
    """
    Orquestra o ciclo de vida de um pedido:
    - Gerencia estado e eventos via WorkflowManager.
    - Executa o grafo LangGraph via WorkflowRunner.
    - Sincroniza interrupções e retomadas.
    """

    def __init__(self):
        self.event_publisher = EventPublisher()
        self.workflow_manager = WorkflowManager(self.event_publisher)
        self.workflow_runner = WorkflowRunner()

    def create_order(self, session_id: str, message: str) -> Dict[str, Any]:
        """Cria um novo pedido e inicia o workflow."""
        # 1. Cria order no WorkflowManager (vai para INTERPRETADO)
        order = self.workflow_manager.create_order(session_id, message)
        print(f">>> [ORCHESTRATOR] Order criada: {order.id}, estado: {order.current_state.value}")

        # 2. Inicia o workflow no LangGraph
        runner_result = self.workflow_runner.start(order.id, session_id, message)
        print(f">>> [ORCHESTRATOR] Runner result: {runner_result}")

        # 3. Se o runner interrompeu, extrai as intenções e avança o estado
        if runner_result["status"] == "interrupted":
            intentions = runner_result.get("intentions", [])
            print(f">>> [ORCHESTRATOR] Intenções extraídas: {intentions}")

            # Publica evento de intenções extraídas
            event = self.event_publisher.create_event(
                order_id=order.id,
                event_type=EventType.INTENTIONS_EXTRACTED.value,
                source="intent_analyzer",
                payload={"intentions": intentions}
            )
            self.event_publisher.publish(event)

            # Avança o estado para AGUARDANDO_CONFIRMACAO usando o método público
            new_state = self.workflow_manager.advance_state(order.id, EventType.INTENTIONS_EXTRACTED)
            print(f">>> [ORCHESTRATOR] Estado após advance_state: {new_state.value}")

        # 4. Retorna o resultado
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

        # 1. Confirma intenções (vai para EM_ELABORACAO)
        self.workflow_manager.confirm_intentions(order_id, confirmed_chips)

        # 2. Retoma o workflow no LangGraph
        runner_result = self.workflow_runner.resume(order_id, confirmed_chips)

        # 3. Se terminou, registra a proposta e finaliza o estado
        if runner_result["status"] == "completed":
            proposal_content = runner_result.get("proposal")
            if proposal_content:
                # Cria a proposta (EM_ELABORACAO -> EM_ANALISE)
                self.workflow_manager.set_proposal(order_id, proposal_content)

                # Avança o estado até o final
                self.workflow_manager.advance_state(order_id, EventType.ANALYSIS_COMPLETED)   # EM_ANALISE -> DECISAO
                self.workflow_manager.advance_state(order_id, EventType.NO_CONFLICT)         # DECISAO -> FINALIZANDO
                self.workflow_manager.finalize_order(order_id, {                             # FINALIZANDO -> FINALIZADO
                    "result": runner_result.get("result"),
                    "proposal": proposal_content,
                })

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

        # Busca a proposta pelo order_id
        proposal_content = None
        for proposal in self.workflow_manager._proposals.values():
            if proposal.order_id == order_id:
                proposal_content = proposal.content
                break

        return {
            "order_id": order_id,
            "status": order.current_state.value,
            "proposal": proposal_content,
            "result": proposal_content,
        }