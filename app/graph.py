import re
from typing import List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from app.llm import ClaimPlan, VerificationResult, plan_with_model, verify_with_model


class IntakeState(TypedDict, total=False):
    question: str
    check_at: str
    public_requested: bool
    category: str
    claim: str
    verification_criteria: List[str]
    verification_plan: str
    model_public_eligible: bool
    public_approved: bool
    model_used: bool


def normalize_input(state: IntakeState) -> IntakeState:
    return {"question": " ".join(state["question"].split())}


def plan_claim(state: IntakeState) -> IntakeState:
    plan = plan_with_model(state["question"], state["check_at"])
    if plan is None:
        plan = _fallback_plan(state["question"])
        model_used = False
    else:
        model_used = True
    return {
        "category": plan.category,
        "claim": plan.claim,
        "verification_criteria": plan.verification_criteria,
        "model_public_eligible": plan.public_eligible,
        "model_used": model_used,
    }


def moderate_publicity(state: IntakeState) -> IntakeState:
    question = state["question"]
    personal_patterns = (
        r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b",
        r"\b1[3-9]\d{9}\b",
        r"身份证",
        r"我(老婆|丈夫|老公|妻子|孩子|同事|老板)",
    )
    rule_safe = not any(
        re.search(pattern, question, re.IGNORECASE) for pattern in personal_patterns
    )
    return {
        "public_approved": bool(state.get("public_requested"))
        and bool(state.get("model_public_eligible"))
        and rule_safe
    }


def build_verification_plan(state: IntakeState) -> IntakeState:
    criteria = "\n".join(
        f"{index + 1}. {item}" for index, item in enumerate(state["verification_criteria"])
    )
    return {
        "verification_plan": (
            f"在 {state['check_at']} 后检查以下声明：{state['claim']}\n"
            f"判断标准：\n{criteria}\n"
            "结论必须为 happened、partially_happened、did_not_happen 或 uncertain。"
        )
    }


def _fallback_plan(question: str) -> ClaimPlan:
    lowered = question.lower()
    categories = (
        ("technology", ("ai", "人工智能", "程序员", "软件", "科技")),
        ("weather", ("weather", "temperature", "天气", "气温")),
        ("career", ("job", "career", "工作", "职业", "招聘")),
        ("finance", ("stock", "market", "股票", "市场", "价格")),
        ("society", ("社会", "政策", "人口", "城市")),
    )
    category = next(
        (name for name, words in categories if any(word in lowered for word in words)),
        "general",
    )
    return ClaimPlan(
        category=category,
        claim=f"在约定验证时间，判断以下预测是否发生：{question}",
        verification_criteria=[
            "查找至少两条相互独立的可靠公开来源",
            "将来源中的事实与原始预测逐项比较",
        ],
        public_eligible=True,
    )


def build_intake_graph():
    graph = StateGraph(IntakeState)
    graph.add_node("normalize_input", normalize_input)
    graph.add_node("plan_claim", plan_claim)
    graph.add_node("moderate_publicity", moderate_publicity)
    graph.add_node("build_verification_plan", build_verification_plan)
    graph.add_edge(START, "normalize_input")
    graph.add_edge("normalize_input", "plan_claim")
    graph.add_edge("plan_claim", "moderate_publicity")
    graph.add_edge("moderate_publicity", "build_verification_plan")
    graph.add_edge("build_verification_plan", END)
    return graph.compile()


class ResolutionState(TypedDict, total=False):
    question: str
    claim: str
    verification_plan: str
    check_at: str
    research: Optional[VerificationResult]
    succeeded: bool
    outcome: str
    summary: str
    evidence: list
    future_letter: str
    error: str


def research_evidence(state: ResolutionState) -> ResolutionState:
    result = verify_with_model(
        question=state["question"],
        claim=state["claim"],
        verification_plan=state["verification_plan"],
        check_at=state["check_at"],
    )
    if result is None:
        return {"research": None, "error": "The research model could not return a valid result."}
    return {"research": result}


def route_research(state: ResolutionState) -> str:
    result = state.get("research")
    if result is None:
        return "failed"
    return "resolved" if result.enough_evidence else "inconclusive"


def finalize_resolution(state: ResolutionState) -> ResolutionState:
    result = state["research"]
    return {
        "succeeded": True,
        "outcome": result.verdict,
        "summary": result.summary.strip(),
        "evidence": [item.model_dump() for item in result.evidence],
        "future_letter": result.future_letter.strip(),
    }


def finalize_inconclusive(state: ResolutionState) -> ResolutionState:
    result = state["research"]
    return {
        "succeeded": True,
        "outcome": "uncertain",
        "summary": result.summary.strip(),
        "evidence": [item.model_dump() for item in result.evidence],
        "future_letter": result.future_letter.strip(),
    }


def mark_research_failed(state: ResolutionState) -> ResolutionState:
    return {"succeeded": False, "error": state.get("error", "Research failed.")}


def build_resolution_graph():
    graph = StateGraph(ResolutionState)
    graph.add_node("research_evidence", research_evidence)
    graph.add_node("finalize_resolution", finalize_resolution)
    graph.add_node("finalize_inconclusive", finalize_inconclusive)
    graph.add_node("mark_research_failed", mark_research_failed)
    graph.add_edge(START, "research_evidence")
    graph.add_conditional_edges(
        "research_evidence",
        route_research,
        {
            "resolved": "finalize_resolution",
            "inconclusive": "finalize_inconclusive",
            "failed": "mark_research_failed",
        },
    )
    graph.add_edge("finalize_resolution", END)
    graph.add_edge("finalize_inconclusive", END)
    graph.add_edge("mark_research_failed", END)
    return graph.compile()


intake_graph = build_intake_graph()
resolution_graph = build_resolution_graph()
