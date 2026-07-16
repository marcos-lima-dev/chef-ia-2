from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.domain.enums import OrderState


class Workflow(BaseModel):
    id: str
    order_id: str
    status: OrderState
    current_step: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None