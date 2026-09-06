import json
import logging
from functools import lru_cache
from typing import List, Literal, Optional

from openai import OpenAI
from pydantic import BaseModel, Field

from app.config import get_settings

logger = logging.getLogger(__name__)


class ClaimPlan(BaseModel):
    category: Literal["technology", "career", "weather", "society", "finance", "general"]
    claim: str
    verification_criteria: List[str] = Field(min_length=1, max_length=5)
    public_eligible: bool
    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    context_summary: str = ""


class EvidenceResult(BaseModel):
    title: str
    url: str
    excerpt: str
    published_at: Optional[str] = None


class VerificationResult(BaseModel):
    enough_evidence: bool
    verdict: Literal["happened", "partially_happened", "did_not_happen", "uncertain"]
    summary: str
    evidence: List[EvidenceResult] = Field(max_length=8)
    future_letter: str


@lru_cache
def get_llm_client() -> Optional[OpenAI]:
    settings = get_settings()
    if not settings.deepseek_api_key:
        return None
    return OpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        timeout=settings.llm_timeout_seconds,
        max_retries=0,
    )


def _structured_response(
    *, name: str, schema: dict, instructions: str, prompt: str, web_search: bool = False
):
    client = get_llm_client()
    if client is None:
        return None

    request = {
        "model": get_settings().deepseek_model,
        "instructions": instructions,
        "input": prompt,
        "reasoning": {"effort": "low"},
        "text": {"format": {"type": "json_schema", "name": name, "schema": schema}},
        "store": False,
    }
    if web_search:
        request["tools"] = [{"type": "web_search"}]

    try:
        response = client.responses.create(**request)
        if not response.output_text:
            return None
        return _load_json(response.output_text)
    except Exception:
        logger.exception("DeepSeek request failed for %s", name)
        return None


def _load_json(output_text: str) -> dict:
    """Accept strict JSON and the occasional fenced JSON returned after tool use."""

    text = output_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end < start:
        raise ValueError("The model response did not contain a JSON object")
    return json.loads(text[start : end + 1])


def plan_with_model(question: str, check_at: str) -> Optional[ClaimPlan]:
    data = _structured_response(
        name="claim_plan",
        schema=ClaimPlan.model_json_schema(),
        instructions=(
            "You are the intake agent for DearFuture. Convert a future-facing question "
            "into one concise, objectively testable claim. Produce concrete verification "
            "criteria suitable for public web evidence. The supplied verification date is "
            "the authoritative deadline: never shift it, extend it, or add another time "
            "period mentioned in the question on top of it. Reject public display for private, "
            "sensitive, defamatory, or personally identifying content. Reply in the same "
            "language as the question.\n\n"
            "Apply a minimum-necessary-context rule. By default, proceed without asking a "
            "follow-up question: use a broad, reasonable interpretation and record it in "
            "context_summary. Do not ask for an exact road, route, minute, or threshold when "
            "a city-level or category-level claim can still be verified. For example, a "
            "question about traffic from Beijing West Railway Station to the Capital Airport "
            "can be evaluated as a broad Beijing route-traffic question. Set "
            "needs_clarification to true only when a missing fact makes the claim genuinely "
            "unverifiable or creates materially different plausible answers, such as a weather "
            "question with no location at all. If clarification is needed, ask exactly one "
            "short, friendly question in clarification_question."
        ),
        prompt=f"Question: {question}\nVerification date: {check_at}",
    )
    if data is None:
        return None
    try:
        return ClaimPlan.model_validate(data)
    except Exception:
        logger.exception("DeepSeek returned an invalid claim plan")
        return None


def verify_with_model(
    *, question: str, claim: str, verification_plan: str, check_at: str
) -> Optional[VerificationResult]:
    data = _structured_response(
        name="verification_result",
        schema=VerificationResult.model_json_schema(),
        web_search=True,
        instructions=(
            "You are DearFuture's research and judgment agent. Search current public web "
            "sources, prefer primary and reputable sources, and compare them with the saved "
            "claim and criteria. Never invent evidence or URLs. If evidence is insufficient, "
            "set enough_evidence to false and verdict to uncertain. Write a concise summary "
            "and a warm future letter in the same language as the original question."
        ),
        prompt=(
            f"Original question: {question}\n"
            f"Saved claim: {claim}\n"
            f"Scheduled verification date: {check_at}\n"
            f"Saved verification plan: {verification_plan}"
        ),
    )
    if data is None:
        return None
    try:
        return VerificationResult.model_validate(data)
    except Exception:
        logger.exception("DeepSeek returned an invalid verification result")
        return None
