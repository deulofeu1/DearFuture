from datetime import datetime, timezone
from typing import List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_serializer,
    field_validator,
)


def _as_utc(value: Optional[datetime]) -> Optional[datetime]:
    """Restore UTC information lost by SQLite's timezone-naive datetime type."""

    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class QuestionCreate(BaseModel):
    question: str = Field(min_length=5, max_length=1000)
    email: Optional[EmailStr] = None
    check_at: datetime
    is_public: bool = True

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("check_at")
    @classmethod
    def check_at_must_be_future(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        if value <= datetime.now(timezone.utc):
            raise ValueError("check_at must be in the future")
        return value


class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    url: str
    excerpt: str
    published_at: Optional[datetime]
    retrieved_at: datetime

    @field_serializer("published_at", "retrieved_at")
    def serialize_dates(self, value: Optional[datetime]) -> Optional[datetime]:
        return _as_utc(value)


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: str
    question: str
    category: str
    claim: str
    verification_criteria: List[str]
    verification_plan: str
    check_at: datetime
    status: str
    is_public: bool
    outcome: Optional[str]
    verification_summary: Optional[str]
    future_letter: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]
    evidence: List[EvidenceRead] = Field(default_factory=list)

    @field_serializer("check_at", "created_at", "resolved_at")
    def serialize_dates(self, value: Optional[datetime]) -> Optional[datetime]:
        return _as_utc(value)


class QuestionCreateResponse(QuestionRead):
    public_request_approved: bool
    message: str


class AdminQuestionRead(BaseModel):
    """Management view with structured intake diagnostics, excluding email."""

    model_config = ConfigDict(from_attributes=True)

    public_id: str
    question: str
    category: str
    claim: str
    verification_criteria: List[str]
    verification_plan: str
    check_at: datetime
    status: str
    is_public: bool
    public_requested: bool
    is_deleted: bool
    model_used: bool
    intake_record: Optional[dict]
    outcome: Optional[str]
    attempt_count: int
    last_attempt_at: Optional[datetime]
    last_error: Optional[str]
    next_attempt_at: Optional[datetime]
    created_at: datetime
    resolved_at: Optional[datetime]
    deleted_at: Optional[datetime]

    @field_serializer(
        "check_at",
        "created_at",
        "resolved_at",
        "deleted_at",
        "next_attempt_at",
        "last_attempt_at",
    )
    def serialize_dates(self, value: Optional[datetime]) -> Optional[datetime]:
        return _as_utc(value)


class AdminActionResponse(BaseModel):
    public_id: str
    status: str
    message: str


class PublicStats(BaseModel):
    total_public: int
    awaiting_future: int
    resolved: int
    happened: int
