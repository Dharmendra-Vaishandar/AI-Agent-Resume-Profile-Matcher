from typing import Dict, List

from utils.parsers import normalize_skill_tokens


class MultiStageEvaluator:
    def __init__(self, requirements: Dict) -> None:
        self.requirements = requirements or {}

    def _evaluate_candidate(self, candidate: Dict) -> Dict:
        must_have = normalize_skill_tokens(self.requirements.get("must_have", []))
        nice_to_have = normalize_skill_tokens(self.requirements.get("nice_to_have", []))
        min_years = int(self.requirements.get("min_experience_years", 0))

        candidate_skills = normalize_skill_tokens(candidate.get("skills", []))
        retrieval_score = float(candidate.get("retrieval_score", 0.0))
        years = int(candidate.get("experience_years", 0))

        must_matches = [skill for skill in must_have if skill in candidate_skills]
        nice_matches = [skill for skill in nice_to_have if skill in candidate_skills]

        must_score = len(must_matches) / max(len(must_have), 1)
        nice_score = len(nice_matches) / max(len(nice_to_have), 1)
        exp_score = min(years / max(min_years, 1), 1.0) if min_years else 1.0

        total_score = (
            0.45 * must_score
            + 0.2 * nice_score
            + 0.2 * exp_score
            + 0.15 * retrieval_score
        )

        strengths = []
        gaps = []

        if must_matches:
            strengths.append(f"Matches must-have skills: {', '.join(must_matches)}")
        if nice_matches:
            strengths.append(f"Matches nice-to-have skills: {', '.join(nice_matches)}")
        if years >= min_years:
            strengths.append(f"Experience meets threshold ({years} years)")

        missing_must = [skill for skill in must_have if skill not in candidate_skills]
        if missing_must:
            gaps.append(f"Missing must-have skills: {', '.join(missing_must)}")
        if years < min_years:
            gaps.append(f"Experience below threshold ({years}/{min_years} years)")

        recommendation = "hire" if total_score >= 0.7 else "no_hire"
        if 0.6 <= total_score < 0.7:
            recommendation = "borderline"

        candidate_eval = {
            **candidate,
            "stage2_score": round(total_score, 4),
            "score_breakdown": {
                "must_have_score": round(must_score, 4),
                "nice_to_have_score": round(nice_score, 4),
                "experience_score": round(exp_score, 4),
                "retrieval_score": round(retrieval_score, 4),
            },
            "strengths": strengths,
            "gaps": gaps,
            "recommendation": recommendation,
        }

        if recommendation == "borderline":
            candidate_eval["improvement_suggestions"] = [
                "Demonstrate hands-on project impact with measurable outcomes.",
                "Strengthen missing must-have areas through focused upskilling.",
            ]

        return candidate_eval

    def evaluate(self, retrieved_candidates: List[Dict]) -> Dict:
        stage1_top10 = retrieved_candidates[:10]
        stage2_deep = [self._evaluate_candidate(candidate) for candidate in stage1_top10]
        ranked = sorted(stage2_deep, key=lambda item: item["stage2_score"], reverse=True)
        shortlist = ranked[:3]

        return {
            "stage1_top10": stage1_top10,
            "stage2_deep_evaluation": ranked,
            "stage3_final_recommendation": shortlist,
        }
