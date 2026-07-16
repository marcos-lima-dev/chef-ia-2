from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.domain.enums import OrderState


class Order(BaseModel):
    id: str
    customer_id: Optional[str] = None
    session_id: str
    original_message: str
    current_state: OrderState = OrderState.RECEBIDO
    workflow_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def change_state(self, new_state: OrderState):
        self.current_state = new_state
        self.updated_at = datetime.now()