from app.graph import intake_graph, resolution_graph
from app.llm import ClaimPlan, EvidenceResult, VerificationResult


def test_intake_graph_builds_a_complete_fallback_plan(monkeypatch):
    monkeypatch.setattr("app.graph.plan_with_model", lambda _question, _check_at: None)
    result = intake_graph.invoke(
        {
            "question": "  AI 会在一个月内取代初级程序员吗？  ",
            "check_at": "2026-10-05T09:00:00+08:00",
            "public_requested": True,
        }
    )

    assert result["question"] == "AI 会在一个月内取代初级程序员吗？"
    assert result["category"] == "technology"
    assert result["verification_criteria"]
    assert result["public_approved"] is True
    assert result["model_used"] is False
    assert result["clarification_required"] is False


def test_intake_graph_only_requests_essential_context(monkeypatch):
    monkeypatch.setattr(
        "app.graph.plan_with_model",
        lambda _question, _check_at: ClaimPlan(
            category="weather",
            claim="指定日期的天气情况可以被核对",
            verification_criteria=["查阅当地权威天气记录"],
            public_eligible=True,
            needs_clarification=True,
            clarification_question="想查哪一个城市的天气呢？",
        ),
    )
    result = intake_graph.invoke(
        {
            "question": "明天会不会下雨？",
            "check_at": "2026-10-05T09:00:00+08:00",
            "public_requested": True,
        }
    )

    assert result["clarification_required"] is True
    assert result["clarification_question"] == "想查哪一个城市的天气呢？"
    assert "public_approved" not in result


def test_intake_graph_combines_model_and_privacy_rules(monkeypatch):
    monkeypatch.setattr(
        "app.graph.plan_with_model",
        lambda _question, _check_at: ClaimPlan(
            category="career",
            claim="一个月后岗位数量下降",
            verification_criteria=["比较公开招聘数据"],
            public_eligible=True,
        ),
    )
    result = intake_graph.invoke(
        {
            "question": "我老婆下个月会不会被公司开除？",
            "check_at": "2026-10-05T09:00:00+08:00",
            "public_requested": True,
        }
    )

    assert result["model_used"] is True
    assert result["public_approved"] is False


def test_resolution_graph_persists_structured_evidence(monkeypatch):
    monkeypatch.setattr(
        "app.graph.verify_with_model",
        lambda **_kwargs: VerificationResult(
            enough_evidence=True,
            verdict="did_not_happen",
            summary="公开数据没有显示预测发生。",
            evidence=[
                EvidenceResult(
                    title="Official report",
                    url="https://example.com/report",
                    excerpt="The measured value stayed below the threshold.",
                )
            ],
            future_letter="你当时的担忧并没有成为现实。",
        ),
    )
    result = resolution_graph.invoke(
        {"question": "Q", "claim": "C", "verification_plan": "P", "check_at": "2026-10-05"}
    )

    assert result["succeeded"] is True
    assert result["outcome"] == "did_not_happen"
    assert result["evidence"][0]["title"] == "Official report"


def test_resolution_graph_marks_model_failure_for_retry(monkeypatch):
    monkeypatch.setattr("app.graph.verify_with_model", lambda **_kwargs: None)
    result = resolution_graph.invoke(
        {"question": "Q", "claim": "C", "verification_plan": "P", "check_at": "2026-10-05"}
    )
    assert result["succeeded"] is False
    assert result["error"]
