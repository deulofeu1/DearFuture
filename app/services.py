from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.db import SessionLocal
from app.email import send_result_email
from app.graph import intake_graph, resolution_graph
from app.models import Evidence, Notification, Question
from app.schemas import QuestionCreate

MAX_VERIFICATION_ATTEMPTS = 3


class QuestionNeedsClarification(ValueError):
    """Raised when intake cannot produce a meaningful claim without one fact."""


def create_question(db: Session, payload: QuestionCreate) -> Question:
    graph_result = intake_graph.invoke(
        {
            "question": payload.question,
            "check_at": payload.check_at.isoformat(),
            "public_requested": payload.is_public,
        }
    )
    if graph_result.get("clarification_required"):
        raise QuestionNeedsClarification(
            graph_result.get("clarification_question")
            or "为了让这封信可以被认真查证，请补充一个关键范围。"
        )
    intake_record = {
        "category": graph_result["category"],
        "claim": graph_result["claim"],
        "verification_criteria": graph_result["verification_criteria"],
        "public_eligible": graph_result["model_public_eligible"],
        "needs_clarification": graph_result.get("needs_clarification", False),
        "clarification_question": graph_result.get("clarification_question"),
        "context_summary": graph_result.get("context_summary", ""),
        "clarification_required": graph_result.get("clarification_required", False),
        "model_used": graph_result["model_used"],
    }
    question = Question(
        question=graph_result["question"],
        email=str(payload.email) if payload.email else None,
        category=graph_result["category"],
        claim=graph_result["claim"],
        verification_criteria=graph_result["verification_criteria"],
        verification_plan=graph_result["verification_plan"],
        check_at=payload.check_at.astimezone(timezone.utc),
        status="scheduled",
        public_requested=payload.is_public,
        is_public=graph_result["public_approved"],
        model_used=graph_result["model_used"],
        intake_record=intake_record,
    )
    db.add(question)
    _commit(db)
    db.refresh(question)
    return question


def get_public_question(db: Session, public_id: str) -> Optional[Question]:
    statement = (
        select(Question)
        .options(selectinload(Question.evidence))
        .where(
            Question.public_id == public_id,
            Question.is_public.is_(True),
            Question.is_deleted.is_(False),
        )
    )
    return db.scalar(statement)


def list_public_questions(
    db: Session, limit: int = 24, category: Optional[str] = None
) -> List[Question]:
    statement = (
        select(Question)
        .options(selectinload(Question.evidence))
        .where(Question.is_public.is_(True), Question.is_deleted.is_(False))
        .order_by(Question.created_at.desc())
        .limit(limit)
    )
    if category:
        statement = statement.where(Question.category == category)
    return list(db.scalars(statement).all())


def get_public_stats(db: Session) -> Dict[str, int]:
    rows = db.execute(
        select(Question.status, Question.outcome, func.count(Question.id))
        .where(Question.is_public.is_(True), Question.is_deleted.is_(False))
        .group_by(Question.status, Question.outcome)
    ).all()
    stats = {"total_public": 0, "awaiting_future": 0, "resolved": 0, "happened": 0}
    for status, outcome, count in rows:
        stats["total_public"] += count
        if status == "resolved":
            stats["resolved"] += count
        else:
            stats["awaiting_future"] += count
        if outcome == "happened":
            stats["happened"] += count
    return stats


def find_due_questions(
    db: Session, now: Optional[datetime] = None, limit: int = 10
) -> List[Question]:
    now = now or datetime.now(timezone.utc)
    statement = (
        select(Question)
        .where(
            Question.is_deleted.is_(False),
            or_(
                (Question.status == "scheduled") & (Question.check_at <= now),
                Question.status == "retry_pending",
            ),
        )
        .order_by(Question.check_at)
        .limit(limit)
    )
    return list(db.scalars(statement).all())


def list_admin_questions(db: Session, status: Optional[str] = None) -> List[Question]:
    statement = select(Question).order_by(Question.created_at.desc()).limit(200)
    if status:
        statement = statement.where(Question.status == status)
    return list(db.scalars(statement).all())


def soft_delete_question(db: Session, public_id: str) -> Optional[Question]:
    question = db.scalar(select(Question).where(Question.public_id == public_id))
    if question is None:
        return None
    question.is_deleted = True
    question.status = "deleted"
    question.deleted_at = datetime.now(timezone.utc)
    _commit(db)
    db.refresh(question)
    return question


def restore_question(db: Session, public_id: str) -> Optional[Question]:
    question = db.scalar(select(Question).where(Question.public_id == public_id))
    if question is None:
        return None
    question.is_deleted = False
    question.deleted_at = None
    question.status = "resolved" if question.resolved_at else "scheduled"
    _commit(db)
    db.refresh(question)
    return question


def retry_question(db: Session, public_id: str) -> Optional[Question]:
    """Mark an unresolved question for an immediate background verification."""

    question = db.scalar(select(Question).where(Question.public_id == public_id))
    if question is None or question.is_deleted or question.status in {"resolved", "verifying"}:
        return None
    question.status = "verifying"
    question.next_attempt_at = None
    question.last_error = None
    question.attempt_count = 0
    _commit(db)
    db.refresh(question)
    return question


def run_manual_retry(public_id: str) -> None:
    """Run a manual retry in a fresh session after the admin response is sent."""

    with SessionLocal() as db:
        question = db.scalar(select(Question).where(Question.public_id == public_id))
        if question is None or question.is_deleted or question.status != "verifying":
            return
        verify_question(db, question)


def recover_interrupted_verifications(db: Session) -> int:
    """Return jobs left in ``verifying`` by a stopped process to the retry queue."""

    interrupted = list(db.scalars(select(Question).where(Question.status == "verifying")).all())
    now = datetime.now(timezone.utc)
    for question in interrupted:
        question.status = "retry_pending"
        question.next_attempt_at = now
        question.last_error = "The previous verification process was interrupted; retrying."
    if interrupted:
        _commit(db)
    return len(interrupted)


def verify_question(db: Session, question: Question) -> Question:
    while question.attempt_count < MAX_VERIFICATION_ATTEMPTS:
        question.status = "verifying"
        question.attempt_count += 1
        question.next_attempt_at = None
        _commit(db)

        result = resolution_graph.invoke(
            {
                "question": question.question,
                "claim": question.claim,
                "verification_plan": question.verification_plan,
                "check_at": question.check_at.isoformat(),
            }
        )

        if not result.get("succeeded"):
            question.last_error = result.get("error", "Verification failed")
            if question.attempt_count < MAX_VERIFICATION_ATTEMPTS:
                continue
            question.status = "failed"
            _commit(db)
            return question

        question.status = "resolved"
        question.outcome = result["outcome"]
        question.verification_summary = result["summary"]
        question.future_letter = result["future_letter"]
        question.resolved_at = datetime.now(timezone.utc)
        question.next_attempt_at = None
        question.last_error = None

        question.evidence.clear()
        for item in result.get("evidence", []):
            question.evidence.append(
                Evidence(
                    title=item["title"][:300],
                    url=item["url"],
                    excerpt=item["excerpt"],
                    published_at=_parse_optional_datetime(item.get("published_at")),
                )
            )
        _commit(db)

        if question.email:
            delivery = send_result_email(
                recipient=question.email,
                question=question.question,
                outcome=question.outcome,
                summary=question.verification_summary,
                letter=question.future_letter,
                public_url=(
                    f"{get_settings().app_base_url}/q/{question.public_id}"
                    if question.is_public
                    else None
                ),
            )
            db.add(
                Notification(
                    question_id=question.id,
                    channel="email",
                    status=delivery.status,
                    error_message=delivery.error,
                    sent_at=datetime.now(timezone.utc) if delivery.status == "sent" else None,
                )
            )
            _commit(db)
        return question

    return question


def process_due_questions(
    db: Session, now: Optional[datetime] = None, limit: int = 10
) -> List[Question]:
    processed = []
    for question in find_due_questions(db, now=now, limit=limit):
        processed.append(verify_question(db, question))
    return processed


def _parse_optional_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _commit(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
