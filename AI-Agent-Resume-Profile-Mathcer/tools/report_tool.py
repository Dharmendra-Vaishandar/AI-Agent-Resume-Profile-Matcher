import json
import os
import re
import urllib.error
import urllib.request
from typing import Dict, List, Optional

from utils.logger import get_logger


logger = get_logger("report_tool")


def _extract_json_block(content: str) -> Optional[Dict]:
    if not content:
        return None

    text = content.strip()
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None

    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _build_prompts(job_description: str, requirements: Dict, shortlist: List[Dict]) -> Dict[str, str]:
    candidate_payload = []
    for candidate in shortlist:
        candidate_payload.append(
            {
                "candidate_id": candidate.get("candidate_id"),
                "name": candidate.get("name"),
                "recommendation": candidate.get("recommendation"),
                "score_breakdown": candidate.get("score_breakdown", {}),
                "strengths": candidate.get("strengths", []),
                "gaps": candidate.get("gaps", []),
                "improvement_suggestions": candidate.get("improvement_suggestions", []),
                "top_sections": candidate.get("top_sections", []),
                "relevant_excerpts": candidate.get("relevant_excerpts", []),
                "experience_years": candidate.get("experience_years", 0),
                "skills": candidate.get("skills", []),
            }
        )

    system_prompt = (
        "You are a hiring assistant. Return ONLY valid JSON with this exact schema: "
        "{\"summary\": string, \"explainability\": [{\"candidate_id\": string, "
        "\"score_breakdown\": object, \"strengths\": string[], \"gaps\": string[], "
        "\"recommendation\": string, \"improvement_suggestions\": string[]}]}"
    )

    user_prompt = (
        "Given this job description, extracted requirements, and shortlisted candidates, "
        "produce a concise summary and explainability list in the exact JSON schema.\n\n"
        f"job_description: {job_description}\n\n"
        f"requirements: {json.dumps(requirements, ensure_ascii=False)}\n\n"
        f"shortlist: {json.dumps(candidate_payload, ensure_ascii=False)}"
    )

    return {"system": system_prompt, "user": user_prompt}


def _synthesize_with_ollama(system_prompt: str, user_prompt: str) -> Optional[Dict]:
    endpoint = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))

    body = {
        "model": model,
        "prompt": f"{system_prompt}\n\n{user_prompt}",
        "stream": False,
        "format": "json",
        "options": {
            "temperature": temperature,
        },
    }

    req = urllib.request.Request(
        f"{endpoint}/api/generate",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        logger.info("Ollama synthesis unavailable: %s", exc)
        return None

    content = payload.get("response", "")
    return _extract_json_block(content)


def _synthesize_with_openai_compatible(system_prompt: str, user_prompt: str) -> Optional[Dict]:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    if not api_key:
        return None

    endpoint = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1/chat/completions").strip()
    model = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))

    body = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        logger.info("OpenAI-compatible synthesis failed: %s", exc)
        return None

    content = (
        payload.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )

    return _extract_json_block(content)


def synthesize_final_report(job_description: str, requirements: Dict, shortlist: List[Dict]) -> Optional[Dict]:
    prompts = _build_prompts(job_description, requirements, shortlist)
    system_prompt = prompts["system"]
    user_prompt = prompts["user"]

    provider = None
    parsed = _synthesize_with_ollama(system_prompt, user_prompt)
    if parsed:
        provider = "ollama"

    if not parsed:
        parsed = _synthesize_with_openai_compatible(system_prompt, user_prompt)
        if parsed:
            provider = "openai_compatible"

    if not parsed:
        logger.info("No LLM synthesis provider available, fallback report used")
        return None

    summary = parsed.get("summary")
    explainability = parsed.get("explainability")
    if not isinstance(summary, str) or not isinstance(explainability, list):
        logger.info("LLM report synthesis returned invalid schema, fallback report used")
        return None

    return {
        "summary": summary,
        "explainability": explainability,
        "_provider": provider,
    }
