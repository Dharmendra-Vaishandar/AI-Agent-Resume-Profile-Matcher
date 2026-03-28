from typing import Any, Dict, List, TypedDict


class AgentState(TypedDict, total=False):
    conversation_history: List[Dict[str, str]]
    job_description: str
    extracted_requirements: Dict[str, Any]
    candidate_pool: List[Dict[str, Any]]
    ranked_candidates: List[Dict[str, Any]]
    shortlist: List[Dict[str, Any]]
    reasoning_log: List[Dict[str, Any]]
    feedback: Dict[str, Any]
    final_report: Dict[str, Any]
    report_provider: str
