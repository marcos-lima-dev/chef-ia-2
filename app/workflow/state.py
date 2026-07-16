from typing import TypedDict, Optional, List, Dict, Any


class WorkflowState(TypedDict, total=False):
    order_id: str
    session_id: str
    original_message: str
    intentions: List[Dict[str, Any]]
    confirmed_chips: List[Dict[str, Any]]
    proposal: Optional[str]
    proposal_version: int
    final_response: Optional[str]
    current_step: str
    error: Optional[str]
   
    _interrupt: bool
    _skip_intent_analyzer: bool
