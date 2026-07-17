from sqlalchemy import Column, String, DateTime, Integer, JSON, Enum, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.infrastructure.database.base import Base
from app.domain.enums import OrderState, EventType, ProposalStatus, AnalysisStatus


class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(String(50), primary_key=True, index=True)
    session_id = Column(String(100), nullable=False)
    original_message = Column(Text, nullable=False)
    current_state = Column(Enum(OrderState), nullable=False, default=OrderState.RECEBIDO)
    workflow_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    workflows = relationship("WorkflowModel", back_populates="order", uselist=False)
    events = relationship("EventModel", back_populates="order")
    proposals = relationship("ProposalModel", back_populates="order")
    analyses = relationship("AnalysisModel", back_populates="order")
    decisions = relationship("DecisionModel", back_populates="order")


class WorkflowModel(Base):
    __tablename__ = "workflows"

    id = Column(String(50), primary_key=True, index=True)
    order_id = Column(String(50), ForeignKey("orders.id"), nullable=False, unique=True)
    status = Column(Enum(OrderState), nullable=False)
    current_step = Column(String(100), nullable=True)
    started_at = Column(DateTime, default=datetime.now, nullable=False)
    finished_at = Column(DateTime, nullable=True)

    order = relationship("OrderModel", back_populates="workflows")


class EventModel(Base):
    __tablename__ = "events"

    id = Column(String(50), primary_key=True, index=True)
    order_id = Column(String(50), ForeignKey("orders.id"), nullable=False)
    type = Column(Enum(EventType), nullable=False)
    source = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.now, nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    version = Column(Integer, default=1)

    order = relationship("OrderModel", back_populates="events")


class ProposalModel(Base):
    __tablename__ = "proposals"

    id = Column(String(50), primary_key=True, index=True)
    order_id = Column(String(50), ForeignKey("orders.id"), nullable=False)
    version = Column(Integer, default=1)
    content = Column(Text, nullable=False)
    status = Column(Enum(ProposalStatus), nullable=False, default=ProposalStatus.DRAFT)
    created_by = Column(String(100), nullable=False, default="chef")
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    order = relationship("OrderModel", back_populates="proposals")


class AnalysisModel(Base):
    __tablename__ = "analyses"

    id = Column(String(50), primary_key=True, index=True)
    order_id = Column(String(50), ForeignKey("orders.id"), nullable=False)
    specialist = Column(String(100), nullable=False)
    status = Column(Enum(AnalysisStatus), nullable=False, default=AnalysisStatus.PENDING)
    summary = Column(Text, nullable=True)
    warnings = Column(JSON, nullable=False, default=list)
    suggestions = Column(JSON, nullable=False, default=list)
    confidence = Column(JSON, nullable=True)  # pode ser um número ou outros dados
    raw_payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    order = relationship("OrderModel", back_populates="analyses")


class DecisionModel(Base):
    __tablename__ = "decisions"

    id = Column(String(50), primary_key=True, index=True)
    order_id = Column(String(50), ForeignKey("orders.id"), nullable=False)
    question = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)
    answer = Column(Text, nullable=True)
    answered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    order = relationship("OrderModel", back_populates="decisions")
