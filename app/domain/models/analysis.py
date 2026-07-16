from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.domain.enums import AnalysisStatus


class Analysis(BaseModel):
    id: str
    order_id: str
    specialist: str
    status: AnalysisStatus = AnalysisStatus.PENDING
    summary: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    confidence: Optional[float] = None
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None