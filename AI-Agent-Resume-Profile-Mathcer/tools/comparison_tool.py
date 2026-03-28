from typing import Dict, List


def compare_candidates(candidate_ids: List[str], ranked_candidates: List[Dict]) -> Dict:
    selected = [candidate for candidate in ranked_candidates if candidate.get("candidate_id") in candidate_ids]

    comparison_rows = []
    for candidate in selected:
        comparison_rows.append(
            {
                "candidate_id": candidate.get("candidate_id"),
                "name": candidate.get("name"),
                "overall_score": candidate.get("stage2_score", 0),
                "must_have_score": candidate.get("score_breakdown", {}).get("must_have_score", 0),
                "experience_years": candidate.get("experience_years", 0),
                "recommendation": candidate.get("recommendation", "no_hire"),
                "strengths": candidate.get("strengths", []),
                "gaps": candidate.get("gaps", []),
            }
        )

    comparison_rows.sort(key=lambda row: row["overall_score"], reverse=True)

    winner = comparison_rows[0]["candidate_id"] if comparison_rows else None

    return {
        "candidate_count": len(comparison_rows),
        "winner": winner,
        "comparison": comparison_rows,
    }
