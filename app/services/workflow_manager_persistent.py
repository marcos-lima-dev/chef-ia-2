from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.services.event_publisher import EventPublisher
from app.services.chip_builder import ChipBuilder
from app.domain.models.order import Order
from app.domain.models.workflow import Workflow
from app.domain.models.event import Event
from app.domain.models.chip import Chip
from app.domain.models.decision import Decision
from app.domain.models.proposal import Proposal
from app.domain.models.analysis import Analysis
from app.domain.enums import OrderState, EventType
from app.domain.state_machine import StateMachine
from app.core.exceptions import OrderNotFoundError, InvalidStateError
from app.infrastructure.database.repositories import (
    OrderRepository,
    WorkflowRepository,
    EventRepository,
    ProposalRepository,
    AnalysisRepository,
    DecisionRepository,
)
import uuid
from datetime import datetime


class WorkflowManagerPersistent:
    """WorkflowManager com persistência em PostgreSQL."""

    def __init__(self, db: Session, event_publisher: EventPublisher):
        self.db = db
        self.event_publisher = event_publisher
        self.order_repo = OrderRepository(db)
        self.workflow_repo = WorkflowRepository(db)
        self.event_repo = EventRepository(db)
        self.proposal_repo = ProposalRepository(db)
        self.analysis_repo = AnalysisRepository(db)
        self.decision_repo = DecisionRepository(db)

    def create_order(self, session_id: str, message: str) -> Order:
        order_id = f"ord_{uuid.uuid4().hex[:12]}"
        order = Order(
            id=order_id,
            session_id=session_id,
            original_message=message,
            current_state=OrderState.RECEBIDO
        )

        workflow = Workflow(
            id=f"wf_{uuid.uuid4().hex[:12]}",
            order_id=order_id,
            status=OrderState.RECEBIDO
        )

        self.order_repo.create(order)
        self.workflow_repo.create(workflow)

        event = self.event_publisher.create_event(
            order_id=order_id,
            event_type=EventType.ORDER_CREATED.value,
            source="workflow_manager",
            payload={"customer_message": message, "session_id": session_id}
        )
        self.event_publisher.publish(event)
        self.event_repo.create(event)

        self._transition(order_id, EventType.ORDER_CREATED)

        return order

    def get_order(self, order_id: str) -> Optional[Order]:
        return self.order_repo.get(order_id)

    def get_chips(self, order_id: str) -> List[Chip]:
        order = self.get_order(order_id)
        if not order:
            raise OrderNotFoundError(f"Pedido {order_id} não encontrado")
        events = self.event_repo.get_by_order(order_id)
        return ChipBuilder.build_from_order(order, events)

    def get_events(self, order_id: str) -> List[Event]:
        return self.event_repo.get_by_order(order_id)

    def advance_state(self, order_id: str, event_type: EventType) -> OrderState:
        return self._transition(order_id, event_type)

    def _transition(self, order_id: str, event_type: EventType) -> OrderState:
        order = self.get_order(order_id)
        if not order:
            raise OrderNotFoundError(f"Pedido {order_id} não encontrado")

        old_state = order.current_state
        new_state = StateMachine.transition(old_state, event_type)

        order.change_state(new_state)
        self.order_repo.update(order)

        workflow = self.workflow_repo.get_by_order(order_id)
        if workflow:
            workflow.status = new_state
            self.workflow_repo.update(workflow)

        state_event = self.event_publisher.create_event(
            order_id=order_id,
            event_type=EventType.STATE_CHANGED.value,
            source="workflow_manager",
            payload={"from": old_state.value, "to": new_state.value}
        )
        self.event_publisher.publish(state_event)
        self.event_repo.create(state_event)

        return new_state

    def confirm_intentions(self, order_id: str, confirmed_chips: List[Dict[str, Any]]) -> Order:
        order = self.get_order(order_id)
        if not order:
            raise OrderNotFoundError(f"Pedido {order_id} não encontrado")

        if order.current_state != OrderState.AGUARDANDO_CONFIRMACAO:
            raise InvalidStateError(
                f"Pedido não está aguardando confirmação. Estado atual: {order.current_state.value}"
            )

        event = self.event_publisher.create_event(
            order_id=order_id,
            event_type=EventType.INTENTIONS_CONFIRMED.value,
            source="workflow_manager",
            payload={"confirmed_chips": confirmed_chips}
        )
        self.event_publisher.publish(event)
        self.event_repo.create(event)

        self._transition(order_id, EventType.INTENTIONS_CONFIRMED)

        return order

    def request_decision(self, order_id: str, question: str, options: List[str]) -> Decision:
        order = self.get_order(order_id)
        if not order:
            raise OrderNotFoundError(f"Pedido {order_id} não encontrado")

        decision = Decision(
            id=f"dec_{uuid.uuid4().hex[:12]}",
            order_id=order_id,
            question=question,
            options=options
        )
        self.decision_repo.create(decision)

        event = self.event_publisher.create_event(
            order_id=order_id,
            event_type=EventType.CUSTOMER_DECISION_REQUIRED.value,
            source="workflow_manager",
            payload={"question": question, "options": options, "decision_id": decision.id}
        )
        self.event_publisher.publish(event)
        self.event_repo.create(event)

        self._transition(order_id, EventType.CONFLICT_FOUND)

        return decision

    def submit_decision(self, order_id: str, decision_id: str, answer: str) -> Order:
        order = self.get_order(order_id)
        if not order:
            raise OrderNotFoundError(f"Pedido {order_id} não encontrado")

        if order.current_state != OrderState.AGUARDANDO_DECISAO:
            raise InvalidStateError(
                f"Pedido não está aguardando decisão. Estado atual: {order.current_state.value}"
            )

        decision = self.decision_repo.get(decision_id)
        if not decision:
            raise ValueError(f"Decisão {decision_id} não encontrada")

        decision.answer = answer
        decision.answered_at = datetime.now()
        self.decision_repo.update(decision)

        event = self.event_publisher.create_event(
            order_id=order_id,
            event_type=EventType.CUSTOMER_DECISION_RECEIVED.value,
            source="workflow_manager",
            payload={"decision_id": decision_id, "answer": answer}
        )
        self.event_publisher.publish(event)
        self.event_repo.create(event)

        self._transition(order_id, EventType.CUSTOMER_DECISION_RECEIVED)

        return order

    def set_proposal(self, order_id: str, content: str) -> Proposal:
        order = self.get_order(order_id)
        if not order:
            raise OrderNotFoundError(f"Pedido {order_id} não encontrado")

        existing = self.proposal_repo.get_by_order(order_id)
        version = 1 if not existing else existing.version + 1

        proposal = Proposal(
            id=f"pro_{uuid.uuid4().hex[:12]}",
            order_id=order_id,
            version=version,
            content=content
        )
        self.proposal_repo.create(proposal)

        event = self.event_publisher.create_event(
            order_id=order_id,
            event_type=EventType.PROPOSAL_CREATED.value,
            source="chef",
            payload={"proposal_id": proposal.id, "version": proposal.version}
        )
        self.event_publisher.publish(event)
        self.event_repo.create(event)

        if order.current_state == OrderState.EM_ELABORACAO:
            self._transition(order_id, EventType.PROPOSAL_CREATED)

        return proposal

    def add_analysis(self, order_id: str, specialist: str, summary: str, warnings: List[str], suggestions: List[str], raw_payload: Dict[str, Any]) -> Analysis:
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
        self.analysis_repo.create(analysis)

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
        self.event_repo.create(event)

        return analysis

    def finalize_order(self, order_id: str, result: Dict[str, Any]) -> Order:
        order = self.get_order(order_id)
        if not order:
            raise OrderNotFoundError(f"Pedido {order_id} não encontrado")

        event = self.event_publisher.create_event(
            order_id=order_id,
            event_type=EventType.RESULT_READY.value,
            source="editor",
            payload=result
        )
        self.event_publisher.publish(event)
        self.event_repo.create(event)

        self._transition(order_id, EventType.FINAL_RESPONSE_CREATED)

        return order
