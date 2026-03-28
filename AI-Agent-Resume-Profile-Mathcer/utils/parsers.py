import re
from typing import Dict, List


SKILL_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9+#.\-]{1,}")
YEARS_PATTERN = re.compile(r"(\d+)\+?\s*(?:years|yrs)", re.IGNORECASE)


def parse_resume_text(candidate_id: str, text: str) -> Dict:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = lines[0] if lines else candidate_id

    skill_section = " ".join(lines)
    skills = sorted({token for token in SKILL_PATTERN.findall(skill_section) if len(token) > 2})

    years = 0
    for match in YEARS_PATTERN.findall(skill_section):
        years = max(years, int(match))

    return {
        "candidate_id": candidate_id,
        "name": name,
        "experience_years": years,
        "skills": skills,
        "raw_text": text,
    }


def normalize_skill_tokens(skills: List[str]) -> List[str]:
    return sorted({skill.strip().lower() for skill in skills if skill.strip()})
