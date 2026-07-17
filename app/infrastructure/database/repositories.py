from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.infrastructure.database.models import (
    OrderModel,
    WorkflowModel,
    EventModel,
    ProposalModel,
    AnalysisModel,
    DecisionModel,
)
from app.domain.models.order import Order
from app.domain.models.workflow import Workflow
from app.domain.models.event import Event
from app.domain.models.proposal import Proposal
from app.domain.models.analysis import Analysis
from app.domain.models.decision import Decision
from app.domain.enums import OrderState, EventType, ProposalStatus, AnalysisStatus


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, order: Order) -> Order:
        db_order = OrderModel(
            id=order.id,
            session_id=order.session_id,
            original_message=order.original_message,
            current_state=order.current_state,
            workflow_id=order.workflow_id,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
        self.db.add(db_order)
        self.db.commit()
        self.db.refresh(db_order)
        return self._to_domain(db_order)

    def get(self, order_id: str) -> Optional[Order]:
        db_order = self.db.query(OrderModel).filter(OrderModel.id == order_id).first()
        if not db_order:
            return None
        return self._to_domain(db_order)

    def update(self, order: Order) -> Order:
        db_order = self.db.query(OrderModel).filter(OrderModel.id == order.id).first()
        if not db_order:
            raise ValueError(f"Order {order.id} not found")
        db_order.current_state = order.current_state
        db_order.workflow_id = order.workflow_id
        db_order.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(db_order)
        return self._to_domain(db_order)

    def _to_domain(self, db_order: OrderModel) -> Order:
        return Order(
            id=db_order.id,
            session_id=db_order.session_id,
            original_message=db_order.original_message,
            current_state=db_order.current_state,
            workflow_id=db_order.workflow_id,
            created_at=db_order.created_at,
            updated_at=db_order.updated_at,
        )


class WorkflowRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, workflow: Workflow) -> Workflow:
        db_workflow = WorkflowModel(
            id=workflow.id,
            order_id=workflow.order_id,
            status=workflow.status,
            current_step=workflow.current_step,
            started_at=workflow.started_at,
            finished_at=workflow.finished_at,
        )
        self.db.add(db_workflow)
        self.db.commit()
        self.db.refresh(db_workflow)
        return self._to_domain(db_workflow)

    def get_by_order(self, order_id: str) -> Optional[Workflow]:
        db_workflow = self.db.query(WorkflowModel).filter(WorkflowModel.order_id == order_id).first()
        if not db_workflow:
            return None
        return self._to_domain(db_workflow)

    def update(self, workflow: Workflow) -> Workflow:
        db_workflow = self.db.query(WorkflowModel).filter(WorkflowModel.order_id == workflow.order_id).first()
        if not db_workflow:
            raise ValueError(f"Workflow for order {workflow.order_id} not found")
        db_workflow.status = workflow.status
        db_workflow.current_step = workflow.current_step
        db_workflow.finished_at = workflow.finished_at
        self.db.commit()
        self.db.refresh(db_workflow)
        return self._to_domain(db_workflow)

    def _to_domain(self, db_workflow: WorkflowModel) -> Workflow:
        return Workflow(
            id=db_workflow.id,
            order_id=db_workflow.order_id,
            status=db_workflow.status,
            current_step=db_workflow.current_step,
            started_at=db_workflow.started_at,
            finished_at=db_workflow.finished_at,
        )


class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, event: Event) -> Event:
        db_event = EventModel(
            id=event.id,
            order_id=event.order_id,
            type=event.type,
            source=event.source,
            timestamp=event.timestamp,
            payload=event.payload,
            version=event.version,
        )
        self.db.add(db_event)
        self.db.commit()
        self.db.refresh(db_event)
        return self._to_domain(db_event)

    def get_by_order(self, order_id: str) -> List[Event]:
        db_events = self.db.query(EventModel).filter(EventModel.order_id == order_id).order_by(EventModel.timestamp).all()
        return [self._to_domain(e) for e in db_events]

    def _to_domain(self, db_event: EventModel) -> Event:
        return Event(
            id=db_event.id,
            order_id=db_event.order_id,
            type=db_event.type,
            source=db_event.source,
            timestamp=db_event.timestamp,
            payload=db_event.payload,
            version=db_event.version,
        )


class ProposalRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, proposal: Proposal) -> Proposal:
        db_proposal = ProposalModel(
            id=proposal.id,
            order_id=proposal.order_id,
            version=proposal.version,
            content=proposal.content,
            status=proposal.status,
            created_by=proposal.created_by,
            created_at=proposal.created_at,
            updated_at=proposal.updated_at,
        )
        self.db.add(db_proposal)
        self.db.commit()
        self.db.refresh(db_proposal)
        return self._to_domain(db_proposal)

    def get_by_order(self, order_id: str) -> Optional[Proposal]:
        db_proposal = self.db.query(ProposalModel).filter(ProposalModel.order_id == order_id).order_by(ProposalModel.version.desc()).first()
        if not db_proposal:
            return None
        return self._to_domain(db_proposal)

    def update(self, proposal: Proposal) -> Proposal:
        db_proposal = self.db.query(ProposalModel).filter(ProposalModel.id == proposal.id).first()
        if not db_proposal:
            raise ValueError(f"Proposal {proposal.id} not found")
        db_proposal.content = proposal.content
        db_proposal.status = proposal.status
        db_proposal.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(db_proposal)
        return self._to_domain(db_proposal)

    def _to_domain(self, db_proposal: ProposalModel) -> Proposal:
        return Proposal(
            id=db_proposal.id,
            order_id=db_proposal.order_id,
            version=db_proposal.version,
            content=db_proposal.content,
            status=db_proposal.status,
            created_by=db_proposal.created_by,
            created_at=db_proposal.created_at,
            updated_at=db_proposal.updated_at,
        )


class AnalysisRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, analysis: Analysis) -> Analysis:
        db_analysis = AnalysisModel(
            id=analysis.id,
            order_id=analysis.order_id,
            specialist=analysis.specialist,
            status=analysis.status,
            summary=analysis.summary,
            warnings=analysis.warnings,
            suggestions=analysis.suggestions,
            confidence=analysis.confidence,
            raw_payload=analysis.raw_payload,
            created_at=analysis.created_at,
            completed_at=analysis.completed_at,
        )
        self.db.add(db_analysis)
        self.db.commit()
        self.db.refresh(db_analysis)
        return self._to_domain(db_analysis)

    def get_by_order(self, order_id: str) -> List[Analysis]:
        db_analyses = self.db.query(AnalysisModel).filter(AnalysisModel.order_id == order_id).all()
        return [self._to_domain(a) for a in db_analyses]

    def _to_domain(self, db_analysis: AnalysisModel) -> Analysis:
        return Analysis(
            id=db_analysis.id,
            order_id=db_analysis.order_id,
            specialist=db_analysis.specialist,
            status=db_analysis.status,
            summary=db_analysis.summary,
            warnings=db_analysis.warnings,
            suggestions=db_analysis.suggestions,
            confidence=db_analysis.confidence,
            raw_payload=db_analysis.raw_payload,
            created_at=db_analysis.created_at,
            completed_at=db_analysis.completed_at,
        )


class DecisionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, decision: Decision) -> Decision:
        db_decision = DecisionModel(
            id=decision.id,
            order_id=decision.order_id,
            question=decision.question,
            options=decision.options,
            answer=decision.answer,
            answered_at=decision.answered_at,
            created_at=decision.created_at,
        )
        self.db.add(db_decision)
        self.db.commit()
        self.db.refresh(db_decision)
        return self._to_domain(db_decision)

    def get(self, decision_id: str) -> Optional[Decision]:
        db_decision = self.db.query(DecisionModel).filter(DecisionModel.id == decision_id).first()
        if not db_decision:
            return None
        return self._to_domain(db_decision)

    def update(self, decision: Decision) -> Decision:
        db_decision = self.db.query(DecisionModel).filter(DecisionModel.id == decision.id).first()
        if not db_decision:
            raise ValueError(f"Decision {decision.id} not found")
        db_decision.answer = decision.answer
        db_decision.answered_at = decision.answered_at
        self.db.commit()
        self.db.refresh(db_decision)
        return self._to_domain(db_decision)

    def _to_domain(self, db_decision: DecisionModel) -> Decision:
        return Decision(
            id=db_decision.id,
            order_id=db_decision.order_id,
            question=db_decision.question,
            options=db_decision.options,
            answer=db_decision.answer,
            answered_at=db_decision.answered_at,
            created_at=db_decision.created_at,
        )
