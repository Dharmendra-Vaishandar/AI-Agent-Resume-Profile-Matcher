from pathlib import Path
from typing import Dict, List, Literal, Optional

from langgraph.graph import END, START, StateGraph

from agent.state import AgentState
from rag.document_store import ResumeStore
from rag.ranker import MultiStageEvaluator
from rag.retriever import ResumeRetriever
from tools.report_tool import synthesize_final_report
from tools.requirements_tool import extract_requirements
from utils.logger import get_logger


logger = get_logger("matching_agent")


class HiringMatchingAgent:
    def __init__(self, resume_dir: str = "data/resumes") -> None:
        self.resume_store = ResumeStore(resume_dir)
        self.candidates = self.resume_store.load()
        self.retriever = ResumeRetriever(self.candidates)
        self.graph = self._build_graph()

    def _append_reasoning(self, state: AgentState, step: str, detail: str) -> None:
        state.setdefault("reasoning_log", []).append({"step": step, "detail": detail})
        logger.info("%s | %s", step, detail)

    def parse_jd(self, state: AgentState) -> AgentState:
        jd_input = state.get("job_description", "")
        if not jd_input:
            raise ValueError("job_description is required")

        is_likely_inline = "\n" in jd_input or len(jd_input) > 240
        if not is_likely_inline:
            try:
                jd_path = Path(jd_input)
                if jd_path.exists() and jd_path.is_file():
                    state["job_description"] = jd_path.read_text(encoding="utf-8")
                    self._append_reasoning(state, "parse_jd", f"Loaded JD from file: {jd_path}")
                    return state
            except OSError:
                pass

        self._append_reasoning(state, "parse_jd", "Using inline JD text")

        return state

    def extract_requirements_node(self, state: AgentState) -> AgentState:
        reqs = extract_requirements(state["job_description"])
        state["extracted_requirements"] = reqs
        self._append_reasoning(state, "extract_requirements", f"Extracted requirements: {reqs}")
        return state

    def search_resumes(self, state: AgentState) -> AgentState:
        req = state.get("extracted_requirements", {})
        query = (
            f"must have: {', '.join(req.get('must_have', []))}; "
            f"nice to have: {', '.join(req.get('nice_to_have', []))}; "
            f"min years: {req.get('min_experience_years', 0)}"
        )
        candidate_pool = self.retriever.retrieve(query=query, top_k=10)
        state["candidate_pool"] = candidate_pool
        self._append_reasoning(state, "search_resumes", f"Retrieved {len(candidate_pool)} candidates")
        return state

    def rank_candidates(self, state: AgentState) -> AgentState:
        evaluator = MultiStageEvaluator(state.get("extracted_requirements", {}))
        evaluation = evaluator.evaluate(state.get("candidate_pool", []))

        state["ranked_candidates"] = evaluation["stage2_deep_evaluation"]
        state["shortlist"] = evaluation["stage3_final_recommendation"]
        self._append_reasoning(
            state,
            "rank_candidates",
            f"Ranked {len(state['ranked_candidates'])} candidates, shortlisted {len(state['shortlist'])}",
        )
        return state

    def generate_report(self, state: AgentState) -> AgentState:
        shortlist = state.get("shortlist", [])
        fallback_report = {
            "summary": f"Generated recommendation from {len(state.get('candidate_pool', []))} candidates.",
            "top_recommendations": shortlist,
            "explainability": [
                {
                    "candidate_id": candidate.get("candidate_id"),
                    "score_breakdown": candidate.get("score_breakdown", {}),
                    "strengths": candidate.get("strengths", []),
                    "gaps": candidate.get("gaps", []),
                    "recommendation": candidate.get("recommendation", "no_hire"),
                    "improvement_suggestions": candidate.get("improvement_suggestions", []),
                }
                for candidate in shortlist
            ],
            "metadata": {"report_provider": "fallback"},
        }

        llm_report = synthesize_final_report(
            job_description=state.get("job_description", ""),
            requirements=state.get("extracted_requirements", {}),
            shortlist=shortlist,
        )

        if llm_report:
            provider = llm_report.get("_provider", "llm")
            state["final_report"] = {
                "summary": llm_report.get("summary", fallback_report["summary"]),
                "top_recommendations": shortlist,
                "explainability": llm_report.get("explainability", fallback_report["explainability"]),
                "metadata": {"report_provider": provider},
            }
            state["report_provider"] = provider
            self._append_reasoning(state, "generate_report", f"Built LLM-synthesized final report via {provider}")
            return state

        state["final_report"] = fallback_report
        state["report_provider"] = "fallback"
        self._append_reasoning(state, "generate_report", "Built explainable final report")
        return state

    def human_feedback(self, state: AgentState) -> AgentState:
        feedback = state.get("feedback", {})
        action = feedback.get("action", "end")

        if action == "update_requirements":
            updates = feedback.get("requirements_update", {})
            current = state.get("extracted_requirements", {})
            merged = {**current, **updates}
            state["extracted_requirements"] = merged
            self._append_reasoning(state, "human_feedback", "Requirements updated from manager feedback")
            # Reset feedback action to prevent infinite loops
            state["feedback"] = {"action": "end"}
        elif action == "rerun":
            self._append_reasoning(state, "human_feedback", "Manager requested rerun")
            # Reset feedback action to prevent infinite loops
            state["feedback"] = {"action": "end"}
        else:
            self._append_reasoning(state, "human_feedback", "No feedback changes, ending flow")

        return state

    def _route_feedback(self, state: AgentState) -> Literal["rerun", "end"]:
        action = state.get("feedback", {}).get("action", "end")
        if action in {"rerun", "update_requirements"}:
            return "rerun"
        return "end"

    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("parse_jd", self.parse_jd)
        graph.add_node("extract_requirements", self.extract_requirements_node)
        graph.add_node("search_resumes", self.search_resumes)
        graph.add_node("rank_candidates", self.rank_candidates)
        graph.add_node("generate_report", self.generate_report)
        graph.add_node("human_feedback", self.human_feedback)

        graph.add_edge(START, "parse_jd")
        graph.add_edge("parse_jd", "extract_requirements")
        graph.add_edge("extract_requirements", "search_resumes")
        graph.add_edge("search_resumes", "rank_candidates")
        graph.add_edge("rank_candidates", "generate_report")
        graph.add_edge("generate_report", "human_feedback")

        graph.add_conditional_edges(
            "human_feedback",
            self._route_feedback,
            {
                "rerun": "search_resumes",
                "end": END,
            },
        )

        return graph.compile()

    def run(self, job_description: str, feedback: Optional[Dict] = None) -> AgentState:
        initial_state: AgentState = {
            "conversation_history": [],
            "job_description": job_description,
            "extracted_requirements": {},
            "candidate_pool": [],
            "ranked_candidates": [],
            "shortlist": [],
            "reasoning_log": [],
            "feedback": feedback or {"action": "end"},
        }
        return self.graph.invoke(initial_state)

    def rerun_with_feedback(self, state: AgentState, feedback: Dict) -> AgentState:
        state["feedback"] = feedback
        return self.graph.invoke(state)

    def get_candidate(self, state: AgentState, candidate_id: str) -> Dict:
        ranked = state.get("ranked_candidates", [])
        return next((candidate for candidate in ranked if candidate.get("candidate_id") == candidate_id), {})

    def compare(self, state: AgentState, candidate_ids: List[str]) -> Dict:
        from tools.comparison_tool import compare_candidates

        return compare_candidates(candidate_ids, state.get("ranked_candidates", []))

    def interview_questions(self, state: AgentState, candidate_id: str) -> Dict:
        from tools.interview_tool import generate_interview_questions

        return generate_interview_questions(candidate_id, state.get("ranked_candidates", []))
