from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class Decision(BaseModel):
    id: str
    order_id: str
    question: str
    options: Optional[List[str]] = None
    answer: Optional[str] = None
    answered_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)