import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.logger import get_logger
from utils.parsers import parse_resume_text


logger = get_logger("integrations")


def _append_repo_path(path_value: Optional[str]) -> None:
    if not path_value:
        return
    p = Path(path_value).expanduser().resolve()
    if p.exists() and str(p) not in sys.path:
        sys.path.append(str(p))


def integrate_milestone_repos() -> None:
    _append_repo_path(os.getenv("MILESTONE1_PATH"))
    _append_repo_path(os.getenv("MILESTONE2_PATH"))


def parse_resume_with_milestone(candidate_id: str, text: str) -> Dict[str, Any]:
    integrate_milestone_repos()
    try:
        from resume_parser import parse_resume  # type: ignore

        parsed = parse_resume(text)
        parsed["candidate_id"] = candidate_id
        return parsed
    except Exception as exc:
        logger.info("Milestone1 parser unavailable, fallback parser used: %s", exc)
        return parse_resume_text(candidate_id, text)


def search_with_milestone(query: str, top_k: int = 10) -> Optional[List[Dict[str, Any]]]:
    integrate_milestone_repos()
    try:
        from rag_pipeline import search_candidates  # type: ignore

        return search_candidates(query=query, top_k=top_k)
    except Exception as exc:
        logger.info("Milestone2 search unavailable, internal retriever used: %s", exc)
        return None
