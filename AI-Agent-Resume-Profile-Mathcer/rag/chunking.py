import re
from collections import defaultdict
from typing import Dict, List, Optional


SECTION_ALIASES: Dict[str, List[str]] = {
    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "career history",
    ],
    "education": ["education", "academic background", "academics", "qualifications"],
    "skills": ["skills", "technical skills", "core skills", "competencies"],
    "projects": ["projects", "project experience", "key projects"],
    "certifications": ["certifications", "licenses", "certificates"],
    "summary": ["summary", "profile", "professional summary", "objective"],
}


def _clean_heading(line: str) -> str:
    return re.sub(r"[^a-zA-Z ]", "", line).strip().lower()


def _detect_section_heading(line: str) -> Optional[str]:
    cleaned = _clean_heading(line)
    if not cleaned:
        return None
    if len(cleaned.split()) > 5:
        return None

    for canonical, aliases in SECTION_ALIASES.items():
        if cleaned in aliases:
            return canonical
        if any(cleaned.startswith(alias) for alias in aliases):
            return canonical
    return None


def split_into_sections(text: str) -> Dict[str, str]:
    sections: Dict[str, List[str]] = defaultdict(list)
    current_section = "general"

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        maybe_section = _detect_section_heading(line)
        if maybe_section:
            current_section = maybe_section
            continue

        sections[current_section].append(line)

    if not sections:
        return {"general": text}
    return {section: "\n".join(lines).strip() for section, lines in sections.items() if lines}


def chunk_section_text(section_text: str, chunk_size_words: int = 220, chunk_overlap_words: int = 40) -> List[str]:
    paragraphs = [part.strip() for part in re.split(r"\n{2,}", section_text) if part.strip()]
    if not paragraphs:
        return []

    chunk_size = max(50, chunk_size_words)
    overlap = max(0, min(chunk_overlap_words, chunk_size // 2))

    chunks: List[str] = []
    current_words: List[str] = []

    def flush_chunk() -> None:
        if current_words:
            chunks.append(" ".join(current_words).strip())

    for paragraph in paragraphs:
        paragraph_words = paragraph.split()
        if not paragraph_words:
            continue

        if len(paragraph_words) >= chunk_size:
            if current_words:
                flush_chunk()
                current_words = []

            step = max(1, chunk_size - overlap)
            for start in range(0, len(paragraph_words), step):
                piece = paragraph_words[start : start + chunk_size]
                if piece:
                    chunks.append(" ".join(piece))
            continue

        if len(current_words) + len(paragraph_words) <= chunk_size:
            current_words.extend(paragraph_words)
        else:
            flush_chunk()
            current_words = current_words[-overlap:] if overlap and current_words else []
            current_words.extend(paragraph_words)

    flush_chunk()
    return [chunk for chunk in chunks if chunk]
