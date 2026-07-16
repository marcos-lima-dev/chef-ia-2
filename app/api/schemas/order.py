from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class OrderCreateRequest(BaseModel):
    message: str


class OrderCreateResponse(BaseModel):
    order_id: str
    status: str
    intentions: List[Dict[str, Any]] = []
    current_step: str = ""


class ChipConfirmRequest(BaseModel):
    chips: List[Dict[str, Any]]


class OrderStateResponse(BaseModel):
    order_id: str
    status: str
    chips: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []


class OrderResultResponse(BaseModel):
    order_id: str
    status: str
    proposal: Optional[str] = None
    result: Optional[str] = None
