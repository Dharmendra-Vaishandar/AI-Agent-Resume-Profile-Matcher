import re
from typing import Dict, List


COMMON_SKILLS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "node",
    "sql",
    "aws",
    "azure",
    "docker",
    "kubernetes",
    "llm",
    "langchain",
    "langgraph",
    "machine learning",
    "data engineering",
    "spark",
}


def _extract_skills(text: str) -> List[str]:
    lowered = text.lower()
    found = []
    for skill in COMMON_SKILLS:
        if skill in lowered:
            found.append(skill)
    return sorted(found)


def extract_requirements(jd: str) -> Dict:
    text = jd.strip()
    lowered = text.lower()

    must_have = []
    nice_to_have = []

    sections = re.split(r"\n+", lowered)
    for section in sections:
        if "must" in section or "required" in section:
            must_have.extend(_extract_skills(section))
        elif "nice" in section or "preferred" in section or "plus" in section:
            nice_to_have.extend(_extract_skills(section))

    if not must_have:
        must_have = _extract_skills(text)[:6]
    if not nice_to_have:
        remaining = [skill for skill in _extract_skills(text) if skill not in must_have]
        nice_to_have = remaining[:4]

    years_match = re.findall(r"(\d+)\+?\s*(?:years|yrs)", lowered)
    min_years = int(years_match[0]) if years_match else 0

    return {
        "must_have": sorted(set(must_have)),
        "nice_to_have": sorted(set(nice_to_have)),
        "min_experience_years": min_years,
    }
