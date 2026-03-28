from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List

from rag.chunking import chunk_section_text, split_into_sections
from utils.integrations import parse_resume_with_milestone


@dataclass
class CandidateProfile:
    candidate_id: str
    name: str
    experience_years: int
    skills: List[str]
    raw_text: str
    chunks: List[Dict]

    def to_dict(self) -> Dict:
        return asdict(self)


class ResumeStore:
    def __init__(self, resume_dir: str) -> None:
        self.resume_dir = Path(resume_dir)
        self.candidates: List[CandidateProfile] = []
        self.chunk_size_words = 220
        self.chunk_overlap_words = 40

    def load(self) -> List[CandidateProfile]:
        self.candidates = []
        if not self.resume_dir.exists():
            return self.candidates

        for file_path in sorted(self.resume_dir.glob("*.txt")):
            text = file_path.read_text(encoding="utf-8")
            parsed = parse_resume_with_milestone(file_path.stem, text)
            raw_text = parsed.get("raw_text", text)

            chunks: List[Dict] = []
            sections = split_into_sections(raw_text)
            for section, section_text in sections.items():
                section_chunks = chunk_section_text(
                    section_text,
                    chunk_size_words=self.chunk_size_words,
                    chunk_overlap_words=self.chunk_overlap_words,
                )
                for idx, chunk_text in enumerate(section_chunks):
                    chunks.append(
                        {
                            "candidate_id": parsed.get("candidate_id", file_path.stem),
                            "section": section,
                            "chunk_index": idx,
                            "text": chunk_text,
                        }
                    )

            if not chunks and raw_text.strip():
                chunks = [
                    {
                        "candidate_id": parsed.get("candidate_id", file_path.stem),
                        "section": "general",
                        "chunk_index": 0,
                        "text": raw_text.strip(),
                    }
                ]

            candidate = CandidateProfile(
                candidate_id=parsed.get("candidate_id", file_path.stem),
                name=parsed.get("name", file_path.stem),
                experience_years=int(parsed.get("experience_years", 0)),
                skills=list(parsed.get("skills", [])),
                raw_text=raw_text,
                chunks=chunks,
            )
            self.candidates.append(candidate)

        return self.candidates
