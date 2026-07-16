from pydantic import BaseModel
from typing import Optional


class Intention(BaseModel):
    type: str
    value: str
    confidence: float = 1.0
    confirmed: bool = False