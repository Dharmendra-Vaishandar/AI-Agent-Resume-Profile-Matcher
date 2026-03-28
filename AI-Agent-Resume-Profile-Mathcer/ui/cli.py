import json
import re
from pathlib import Path
from typing import Dict, List

from rich.console import Console
from rich.table import Table

from agent.matching_agent import HiringMatchingAgent


console = Console()


def _print_report_provider(state: Dict) -> None:
    provider = (
        state.get("report_provider")
        or state.get("final_report", {}).get("metadata", {}).get("report_provider")
        or "fallback"
    )
    console.print(f"Report source: {provider}")


def _print_ranked_candidates(candidates: List[Dict]) -> None:
    table = Table(title="Ranked Candidates")
    table.add_column("Rank")
    table.add_column("Candidate ID")
    table.add_column("Name")
    table.add_column("Score")
    table.add_column("Recommendation")

    for idx, candidate in enumerate(candidates, start=1):
        table.add_row(
            str(idx),
            candidate.get("candidate_id", "-"),
            candidate.get("name", "-"),
            str(candidate.get("stage2_score", 0)),
            candidate.get("recommendation", "-"),
        )
    console.print(table)


def _show_help() -> None:
    console.print(
        """
Commands:
- run <jd_path_or_inline_text>
- show shortlist
- find <query>
- compare <candidate_id_1,candidate_id_2,...>
- why <candidate_id>
- questions <candidate_id>
- update must=<skill1,skill2> nice=<skill3,skill4> years=<n>
- rerank
- state
- exit
"""
    )


def _parse_update_command(command: str) -> Dict:
    updates: Dict = {}
    must_match = re.search(r"must=([^ ]+)", command)
    nice_match = re.search(r"nice=([^ ]+)", command)
    years_match = re.search(r"years=(\d+)", command)

    if must_match:
        updates["must_have"] = [item.strip() for item in must_match.group(1).split(",") if item.strip()]
    if nice_match:
        updates["nice_to_have"] = [item.strip() for item in nice_match.group(1).split(",") if item.strip()]
    if years_match:
        updates["min_experience_years"] = int(years_match.group(1))

    return updates


def run_cli() -> None:
    agent = HiringMatchingAgent(resume_dir="data/resumes")
    state: Dict = {
        "conversation_history": [],
        "job_description": "",
        "extracted_requirements": {},
        "candidate_pool": [],
        "ranked_candidates": [],
        "shortlist": [],
        "reasoning_log": [],
        "feedback": {"action": "end"},
    }

    console.print("\n[bold green]AI Hiring Assistant (LangGraph)[/bold green]")
    _show_help()

    while True:
        user_input = console.input("\n[bold cyan]manager> [/bold cyan]").strip()
        if not user_input:
            continue

        state.setdefault("conversation_history", []).append({"role": "user", "content": user_input})

        if user_input.lower() == "exit":
            console.print("Exiting assistant.")
            break

        if user_input.lower() == "help":
            _show_help()
            continue

        if user_input.startswith("run "):
            jd_arg = user_input[4:].strip()
            jd_path = Path(jd_arg)
            jd_value = jd_path.read_text(encoding="utf-8") if jd_path.exists() else jd_arg
            state = agent.run(jd_value)
            console.print("Pipeline executed successfully.")
            _print_report_provider(state)
            _print_ranked_candidates(state.get("ranked_candidates", []))
            continue

        if user_input.lower() == "show shortlist":
            _print_ranked_candidates(state.get("shortlist", []))
            continue

        if user_input.startswith("find "):
            query = user_input[5:].strip()
            found = agent.retriever.retrieve(query=query, top_k=10)
            console.print(f"Found {len(found)} candidates for query: {query}")
            _print_ranked_candidates(found)
            continue

        if user_input.startswith("compare "):
            raw_ids = user_input[8:].strip()
            ids = [candidate_id.strip() for candidate_id in raw_ids.split(",") if candidate_id.strip()]
            comparison = agent.compare(state, ids)
            console.print_json(json.dumps(comparison, indent=2))
            continue

        if user_input.startswith("why "):
            candidate_id = user_input[4:].strip()
            candidate = agent.get_candidate(state, candidate_id)
            if not candidate:
                console.print(f"Candidate '{candidate_id}' not found in ranked list.")
                continue

            explanation = {
                "candidate_id": candidate_id,
                "score_breakdown": candidate.get("score_breakdown", {}),
                "strengths": candidate.get("strengths", []),
                "gaps": candidate.get("gaps", []),
                "recommendation": candidate.get("recommendation", "no_hire"),
            }
            console.print_json(json.dumps(explanation, indent=2))
            continue

        if user_input.startswith("questions "):
            candidate_id = user_input[10:].strip()
            question_pack = agent.interview_questions(state, candidate_id)
            console.print_json(json.dumps(question_pack, indent=2))
            continue

        if user_input.startswith("update "):
            updates = _parse_update_command(user_input)
            if not updates:
                console.print("No valid updates found. Example: update must=react,python nice=aws years=3")
                continue

            state = agent.rerun_with_feedback(
                state,
                {
                    "action": "update_requirements",
                    "requirements_update": updates,
                },
            )
            console.print(f"Updated requirements and reran pipeline: {updates}")
            _print_report_provider(state)
            _print_ranked_candidates(state.get("ranked_candidates", []))
            continue

        if user_input.lower() == "rerank":
            state = agent.rerun_with_feedback(state, {"action": "rerun"})
            console.print("Rerun complete.")
            _print_report_provider(state)
            _print_ranked_candidates(state.get("ranked_candidates", []))
            continue

        if user_input.lower() == "state":
            console.print_json(json.dumps(state, indent=2))
            continue

        console.print("I did not understand that command. Type 'help'.")
