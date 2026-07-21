from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class IngredientEntity(BaseModel):
    id: str
    canonical_name: str
    slug: str
    category: Optional[str] = None
    edible: bool = True
    aliases: List[str] = []
    nutritional_info: Dict[str, Any] = {}
    seasonality: List[str] = []
    properties: Dict[str, Any] = {}
