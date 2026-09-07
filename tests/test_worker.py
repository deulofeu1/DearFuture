from datetime import datetime, timedelta, timezone

from app.email import DeliveryResult
from app.models import Question
from app.services import (
    find_due_questions,
    process_due_questions,
    recover_interrupted_verifications,
)


def make_question(*, check_at, status="scheduled") -> Question:
    return Question(
        question="Will this happen?",
        email="demo@example.com",
        category="general",
        claim="This will happen.",
        verification_criteria=["Check public evidence"],
        verification_plan="Check public evidence.",
        check_at=check_at,
        status=status,
        public_requested=True,
        is_public=True,
        model_used=False,
    )


class SuccessfulGraph:
    def invoke(self, _state):
        return {
            "succeeded": True,
            "outcome": "happened",
            "summary": "The prediction happened.",
            "future_letter": "Reality arrived.",
            "evidence": [
                {
                    "title": "Primary source",
                    "url": "https://example.com/source",
                    "excerpt": "The event was confirmed.",
                    "published_at": None,
                }
            ],
        }


class FailedGraph:
    def invoke(self, _state):
        return {"succeeded": False, "error": "temporary model error"}


def test_worker_resolves_only_due_questions(db, monkeypatch):
    now = datetime.now(timezone.utc)
    due = make_question(check_at=now - timedelta(minutes=1))
    future = make_question(check_at=now + timedelta(days=1))
    db.add_all([due, future])
    db.commit()
    monkeypatch.setattr("app.services.resolution_graph", SuccessfulGraph())
    monkeypatch.setattr(
        "app.services.send_result_email", lambda **_kwargs: DeliveryResult(status="skipped")
    )

    processed = process_due_questions(db, now=now)

    assert [item.id for item in processed] == [due.id]
    assert due.status == "resolved"
    assert due.outcome == "happened"
    assert due.evidence[0].title == "Primary source"
    assert due.notifications[0].status == "skipped"
    assert future.status == "scheduled"


def test_failed_verification_retries_immediately_three_times(db, monkeypatch):
    now = datetime.now(timezone.utc)
    question = make_question(check_at=now - timedelta(minutes=1))
    db.add(question)
    db.commit()
    monkeypatch.setattr("app.services.resolution_graph", FailedGraph())

    process_due_questions(db, now=now)

    assert question.status == "failed"
    assert question.attempt_count == 3
    assert question.next_attempt_at is None


def test_old_retry_pending_question_is_picked_up_without_waiting_for_old_deadline(db):
    question = make_question(
        check_at=datetime.now(timezone.utc) + timedelta(days=1), status="retry_pending"
    )
    question.next_attempt_at = datetime.now(timezone.utc) + timedelta(hours=6)
    db.add(question)
    db.commit()

    assert find_due_questions(db, now=datetime.now(timezone.utc)) == [question]


def test_deleted_question_is_not_picked_up_by_scheduler(db):
    question = make_question(
        check_at=datetime.now(timezone.utc) - timedelta(minutes=1), status="deleted"
    )
    question.is_deleted = True
    db.add(question)
    db.commit()

    assert find_due_questions(db) == []


def test_interrupted_verification_is_recovered_on_startup(db):
    question = make_question(
        check_at=datetime.now(timezone.utc) - timedelta(minutes=1), status="verifying"
    )
    db.add(question)
    db.commit()

    recovered = recover_interrupted_verifications(db)

    assert recovered == 1
    assert question.status == "retry_pending"
    assert question.next_attempt_at is not None
