from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.domain.enums import ChipState, ChipCategory


class Chip(BaseModel):
    id: str
    label: str
    category: ChipCategory
    state: ChipState = ChipState.ACTIVE
    metadata: Optional[Dict[str, Any]] = None