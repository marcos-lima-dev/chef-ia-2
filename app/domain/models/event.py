from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Dict, Optional
from app.domain.enums import EventType


class Event(BaseModel):
    id: str
    order_id: str
    type: EventType
    source: str
    timestamp: datetime = Field(default_factory=datetime.now)
    payload: Dict[str, Any] = Field(default_factory=dict)
    version: int = 1