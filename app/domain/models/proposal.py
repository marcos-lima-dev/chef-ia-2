from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.domain.enums import ProposalStatus


class Proposal(BaseModel):
    id: str
    order_id: str
    version: int = 1
    content: str
    status: ProposalStatus = ProposalStatus.DRAFT
    created_by: str = "chef"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)