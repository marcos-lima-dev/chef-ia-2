from typing import Optional, List, Dict, Any
from app.domain.models.order import Order
from app.domain.models.workflow import Workflow
from app.domain.models.event import Event
from app.domain.models.chip import Chip
from app.domain.models.decision import Decision
from app.domain.models.proposal import Proposal
from app.domain.models.analysis import Analysis
from app.domain.enums import OrderState, EventType
from app.domain.state_machine import StateMachine
from app.services.chip_builder import ChipBuilder
from app.services.event_publisher import EventPublisher
from app.core.exceptions import OrderNotFoundError, InvalidStateError
import uuid
from datetime import datetime


class WorkflowManager:
    """Gerencia o ciclo de vida de um pedido."""

    def __init__(self, event_publisher: EventPublisher):
        self.event_publisher = event_publisher
        self._orders: Dict[str, Order] = {}  # Futuramente substituído por DB
        self._workflows: Dict[str, Workflow] = {}
        self._proposals: Dict[str, Proposal] = {}
        self._analyses: Dict[str, Analysis] = {}
        self._decisions: Dict[str, Decision] = {}

    def create_order(self, session_id: str, message: str) -> Order:
        """Cria um novo pedido."""
        order_id = f"ord_{uuid.uuid4().hex[:12]}"
        order = Order(
            id=order_id,
            session_id=session_id,
            original_message=message,
            current_state=OrderState.RECEBIDO
        )

        # Cria workflow
        workflow = Workflow(
            id=f"wf_{uuid.uuid4().hex[:12]}",
            order_id=order_id,
            status=OrderState.RECEBIDO
        )

        self._orders[order_id] = order
        self._workflows[order_id] = workflow

        # Publica evento de criação
        event = self.event_publisher.create_event(
            order_id=order_id,
            event_type=EventType.ORDER_CREATED.value,
            source="workflow_manager",
            payload={"customer_message": message, "session_id": session_id}
        )
        self.event_publisher.publish(event)

        # Transição para próximo estado (RECEBIDO -> INTERPRETADO)
        self._transition(order_id, EventType.ORDER_CREATED)

        return order

    def get_order(self, order_id: str) -> Optional[Order]:
        """Busca um pedido pelo ID."""
        return self._orders.get(order_id)

    def get_chips(self, order_id: str) -> List[Chip]:
        """Retorna os chips atuais para um pedido."""
        order = self.get_order(order_id)
        if not order:
            raise OrderNotFoundError(f"Pedido {order_id} não encontrado")

        events = self.event_publisher.get_events(order_id)
        return ChipBuilder.build_from_order(order, events)

    def get_events(self, order_id: str) -> List[Event]:
        """Retorna todos os eventos de um pedido."""
        return self.event_publisher.get_events(order_id)

    def _transition(self, order_id: str, event_type: EventType) -> OrderState:
        """Aplica uma transição de estado."""
        order = self.get_order(order_id)
        if not order:
            raise OrderNotFoundError(f"Pedido {order_id} não encontrado")

        old_state = order.current_state
        new_state = StateMachine.transition(old_state, event_type)

        # Atualiza estado
        order.change_state(new_state)
        self._workflows[order_id].status = new_state

        # Registra evento de mudança de estado
        state_event = self.event_publisher.create_event(
            order_id=order_id,
            event_type=EventType.STATE_CHANGED.value,
            source="workflow_manager",
            payload={"from": old_state.value, "to": new_state.value}
        )
        self.event_publisher.publish(state_event)

        return new_state

    def confirm_intentions(self, order_id: str, confirmed_chips: List[Dict[str, Any]]) -> Order:
        """Confirma as intenções do cliente."""
        order = self.get_order(order_id)
        if not order:
            raise OrderNotFoundError(f"Pedido {order_id} não encontrado")

        if order.current_state != OrderState.AGUARDANDO_CONFIRMACAO:
            raise InvalidStateError(
                f"Pedido não está aguardando confirmação. Estado atual: {order.current_state.value}"
            )

        # Registra evento de confirmação
        event = self.event_publisher.create_event(
            order_id=order_id,
            event_type=EventType.INTENTIONS_CONFIRMED.value,
            source="workflow_manager",
            payload={"confirmed_chips": confirmed_chips}
        )
        self.event_publisher.publish(event)

        # Transição para EM_ELABORACAO
        self._transition(order_id, EventType.INTENTIONS_CONFIRMED)

        return order

    def request_decision(self, order_id: str, question: str, options: List[str]) -> Decision:
        """Solicita uma decisão do cliente."""
        order = self.get_order(order_id)
        if not order:
            raise OrderNotFoundError(f"Pedido {order_id} não encontrado")

        # Cria decision
        decision = Decision(
            id=f"dec_{uuid.uuid4().hex[:12]}",
            order_id=order_id,
            question=question,
            options=options
        )
        self._decisions[decision.id] = decision

        # Publica evento de decisão necessária
        event = self.event_publisher.create_event(
            order_id=order_id,
            event_type=EventType.CUSTOMER_DECISION_REQUIRED.value,
            source="workflow_manager",
            payload={"question": question, "options": options, "decision_id": decision.id}
        )
        self.event_publisher.publish(event)

        # Transição para AGUARDANDO_DECISAO
        self._transition(order_id, EventType.CONFLICT_FOUND)

        return decision

    def submit_decision(self, order_id: str, decision_id: str, answer: str) -> Order:
        """Submete a decisão do cliente."""
        order = self.get_order(order_id)
        if not order:
            raise OrderNotFoundError(f"Pedido {order_id} não encontrado")

        if order.current_state != OrderState.AGUARDANDO_DECISAO:
            raise InvalidStateError(
                f"Pedido não está aguardando decisão. Estado atual: {order.current_state.value}"
            )

        # Atualiza a decisão
        decision = self._decisions.get(decision_id)
        if not decision:
            raise ValueError(f"Decisão {decision_id} não encontrada")

        decision.answer = answer
        decision.answered_at = datetime.now()

        # Publica evento de decisão recebida
        event = self.event_publisher.create_event(
            order_id=order_id,
            event_type=EventType.CUSTOMER_DECISION_RECEIVED.value,
            source="workflow_manager",
            payload={"decision_id": decision_id, "answer": answer}
        )
        self.event_publisher.publish(event)

        # Transição para EM_REVISAO
        self._transition(order_id, EventType.CUSTOMER_DECISION_RECEIVED)

        return order

    def set_proposal(self, order_id: str, content: str) -> Proposal:
        """Define a proposta para um pedido."""
        order = self.get_order(order_id)
        if not order:
            raise OrderNotFoundError(f"Pedido {order_id} não encontrado")

        proposal = Proposal(
            id=f"pro_{uuid.uuid4().hex[:12]}",
            order_id=order_id,
            content=content
        )
        self._proposals[proposal.id] = proposal

        # Publica evento de proposta criada
        event = self.event_publisher.create_event(
            order_id=order_id,
            event_type=EventType.PROPOSAL_CREATED.value,
            source="chef",
            payload={"proposal_id": proposal.id, "version": proposal.version}
        )
        self.event_publisher.publish(event)

        # Transição para EM_ANALISE (se ainda não estiver)
        if order.current_state == OrderState.EM_ELABORACAO:
            self._transition(order_id, EventType.PROPOSAL_CREATED)

        return proposal

    def add_analysis(self, order_id: str, specialist: str, summary: str, warnings: List[str], suggestions: List[str], raw_payload: Dict[str, Any]) -> Analysis:
        """Adiciona uma análise de um especialista."""
        order = self.get_order(order_id)
        if not order:
            raise OrderNotFoundError(f"Pedido {order_id} não encontrado")

        analysis = Analysis(
            id=f"ana_{uuid.uuid4().hex[:12]}",
            order_id=order_id,
            specialist=specialist,
            summary=summary,
            warnings=warnings,
            suggestions=suggestions,
            raw_payload=raw_payload,
            status="COMPLETED",
            completed_at=datetime.now()
        )
        self._analyses[analysis.id] = analysis

        # Publica evento de análise concluída
        event = self.event_publisher.create_event(
            order_id=order_id,
            event_type=EventType.ANALYSIS_COMPLETED.value,
            source=specialist,
            payload={
                "analysis_id": analysis.id,
                "summary": summary,
                "warnings": warnings,
                "suggestions": suggestions
            }
        )
        self.event_publisher.publish(event)

        return analysis

    def finalize_order(self, order_id: str, result: Dict[str, Any]) -> Order:
        """Finaliza o pedido."""
        order = self.get_order(order_id)
        if not order:
            raise OrderNotFoundError(f"Pedido {order_id} não encontrado")

        # Publica evento de resultado pronto
        event = self.event_publisher.create_event(
            order_id=order_id,
            event_type=EventType.RESULT_READY.value,
            source="editor",
            payload=result
        )
        self.event_publisher.publish(event)

        # Transição para FINALIZADO
        self._transition(order_id, EventType.FINAL_RESPONSE_CREATED)

        return order