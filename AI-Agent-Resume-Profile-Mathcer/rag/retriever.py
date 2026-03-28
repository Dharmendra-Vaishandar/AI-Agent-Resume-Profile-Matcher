from typing import Dict, List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from rag.document_store import CandidateProfile
from utils.embedding_model import EmbeddingModel
from utils.integrations import search_with_milestone


class ResumeRetriever:
    def __init__(self, candidates: List[CandidateProfile]) -> None:
        self.candidates = candidates
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.initial_candidate_chunks = 60
        self.embedding_weight = 0.6
        self.candidate_by_id = {candidate.candidate_id: candidate for candidate in candidates}
        self.embedder = EmbeddingModel()

        self.chunk_records: List[Dict] = []
        for candidate in candidates:
            for chunk in candidate.chunks:
                self.chunk_records.append(
                    {
                        "candidate_id": candidate.candidate_id,
                        "name": candidate.name,
                        "skills": candidate.skills,
                        "experience_years": candidate.experience_years,
                        "section": chunk.get("section", "general"),
                        "chunk_index": chunk.get("chunk_index", 0),
                        "text": chunk.get("text", ""),
                    }
                )

        self.chunk_texts = [record["text"] for record in self.chunk_records]
        self.doc_matrix = self.vectorizer.fit_transform(self.chunk_texts) if self.chunk_records else None
        self.chunk_embeddings = self.embedder.encode(self.chunk_texts) if self.chunk_texts else None

    @staticmethod
    def _semantic_score(similarities: List[float]) -> float:
        if not similarities:
            return 0.0
        ordered = sorted(similarities, reverse=True)
        best = ordered[0]
        top_three = ordered[:3]
        avg_top = sum(top_three) / len(top_three)
        return max(0.0, min(1.0, 0.7 * best + 0.3 * avg_top))

    @staticmethod
    def _relevant_excerpts(chunk_hits: List[Dict], max_items: int = 3) -> List[str]:
        ordered = sorted(chunk_hits, key=lambda item: item["similarity"], reverse=True)
        excerpts: List[str] = []
        seen = set()
        for hit in ordered:
            text = " ".join(str(hit.get("text", "")).split()).strip()
            if not text:
                continue
            excerpt = text[:220] + ("..." if len(text) > 220 else "")
            if excerpt in seen:
                continue
            seen.add(excerpt)
            excerpts.append(excerpt)
            if len(excerpts) >= max_items:
                break
        return excerpts

    @staticmethod
    def _top_sections(chunk_hits: List[Dict], max_sections: int = 3) -> List[str]:
        sections: List[str] = []
        for hit in sorted(chunk_hits, key=lambda item: item["similarity"], reverse=True):
            section = str(hit.get("section", "general"))
            if section not in sections:
                sections.append(section)
            if len(sections) >= max_sections:
                break
        return sections

    def retrieve(self, query: str, top_k: int = 10) -> List[Dict]:
        external_results = search_with_milestone(query, top_k=top_k)
        if external_results:
            return external_results

        if not self.candidates or self.doc_matrix is None or not self.chunk_records:
            return []

        query_vec = self.vectorizer.transform([query])
        lexical_sims = cosine_similarity(query_vec, self.doc_matrix).flatten()

        sims = lexical_sims
        if self.embedder.enabled and self.chunk_embeddings is not None:
            query_embedding = self.embedder.encode([query])
            if query_embedding is not None and len(query_embedding) > 0:
                embedding_sims = np.dot(self.chunk_embeddings, query_embedding[0])
                sims = (
                    self.embedding_weight * embedding_sims
                    + (1.0 - self.embedding_weight) * lexical_sims
                )

        ranked_chunk_indices = sims.argsort()[::-1][: self.initial_candidate_chunks]

        candidate_hits: Dict[str, List[Dict]] = {}
        for idx in ranked_chunk_indices:
            record = self.chunk_records[idx]
            candidate_id = record["candidate_id"]
            candidate_hits.setdefault(candidate_id, []).append(
                {
                    **record,
                    "similarity": float(sims[idx]),
                }
            )

        aggregated: List[Dict] = []
        for candidate_id, hits in candidate_hits.items():
            candidate = self.candidate_by_id[candidate_id]
            similarities = [float(hit["similarity"]) for hit in hits]
            semantic_score = self._semantic_score(similarities)
            aggregated.append(
                {
                    **candidate.to_dict(),
                    "retrieval_score": round(semantic_score, 4),
                    "top_sections": self._top_sections(hits),
                    "relevant_excerpts": self._relevant_excerpts(hits),
                    "chunk_hit_count": len(hits),
                }
            )

        aggregated.sort(key=lambda item: item["retrieval_score"], reverse=True)
        return aggregated[:top_k]
