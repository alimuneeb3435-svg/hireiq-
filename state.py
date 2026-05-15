from typing import TypedDict, Optional, List, Dict, Any

class HireIQState(TypedDict):
    person_type:      Optional[str]
    name:             Optional[str]
    email:            Optional[str]
    cv_text:          Optional[str]
    cv_path:          Optional[str]
    cv_received:      bool
    job_role:         Optional[str]
    interview_state:  Optional[dict]
    interview_result: Optional[str]
    client_question:  Optional[str]
    rag_answer:       Optional[str]
    preferred_time:   Optional[str]
    guide_available:  Optional[bool]
    assigned_guide:   Optional[str]
    visit_slot:       Optional[str]
    pending_day:      Optional[str]
    pending_time:     Optional[str]
    messages:         List[dict]
    current_node:     str
    error_count:      int
    conversation_done: bool
    response:         str