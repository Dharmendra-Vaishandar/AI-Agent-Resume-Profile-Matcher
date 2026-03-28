from typing import Dict, List


def generate_interview_questions(candidate_id: str, ranked_candidates: List[Dict]) -> Dict:
    candidate = next(
        (profile for profile in ranked_candidates if profile.get("candidate_id") == candidate_id),
        None,
    )

    if not candidate:
        return {
            "candidate_id": candidate_id,
            "questions": ["Candidate not found. Re-run ranking and try again."],
        }

    strengths = candidate.get("strengths", [])
    gaps = candidate.get("gaps", [])
    skills = candidate.get("skills", [])[:4]

    questions = [
        f"Walk us through your most impactful project involving {skills[0] if skills else 'core stack'}.",
        "Describe a complex problem you solved under delivery pressure and your decision process.",
        "How do you ensure production reliability and measurable business outcomes?",
        "What trade-offs did you make in system design decisions, and why?",
        "How do you collaborate with product and cross-functional stakeholders?",
    ]

    for gap in gaps[:2]:
        questions.append(f"You seem to have a gap in: '{gap}'. How would you close it in the first 60 days?")

    if strengths:
        questions.append(f"You show strength in: '{strengths[0]}'. Share a concrete example with metrics.")

    return {
        "candidate_id": candidate_id,
        "questions": questions[:7],
    }
