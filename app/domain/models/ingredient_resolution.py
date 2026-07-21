from typing import Optional, List
from pydantic import BaseModel

from app.domain.models.ingredient import IngredientEntity


class IngredientResolution(BaseModel):
    original_input: str
    normalized_input: Optional[str] = None
    entity: Optional[IngredientEntity] = None
    resolution: str  # "resolved" | "suggested" | "unknown" | "rejected"
    match_confidence: float = 0.0
    reason: str = ""
    suggestions: List[str] = []
    action: str  # "continue" | "needs_confirmation" | "block"
