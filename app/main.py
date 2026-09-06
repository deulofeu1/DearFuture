import asyncio
import secrets
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal, get_db, init_db
from app.llm import get_llm_client
from app.scheduler import run_scheduler
from app.schemas import (
    AdminActionResponse,
    AdminQuestionRead,
    PublicStats,
    QuestionCreate,
    QuestionCreateResponse,
    QuestionRead,
)
from app.services import (
    create_question,
    get_public_question,
    get_public_stats,
    list_admin_questions,
    list_public_questions,
    recover_interrupted_verifications,
    restore_question,
    retry_question,
    run_manual_retry,
    soft_delete_question,
)

STATIC_DIR = Path(__file__).parent / "static"


def require_admin(authorization: Optional[str]) -> None:
    """Protect management APIs with a bearer token kept outside the repository."""

    configured_token = get_settings().admin_token
    if not configured_token:
        raise HTTPException(status_code=503, detail="Admin access is not configured")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Admin authorization is required")

    provided_token = authorization.removeprefix("Bearer ").strip()
    if not secrets.compare_digest(provided_token, configured_token):
        raise HTTPException(status_code=403, detail="Invalid admin token")


def create_app(*, initialize_database: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        scheduler_task = None
        if initialize_database:
            init_db()
            with SessionLocal() as db:
                recover_interrupted_verifications(db)
            if get_settings().scheduler_enabled:
                scheduler_task = asyncio.create_task(run_scheduler())
        try:
            yield
        finally:
            if scheduler_task is not None:
                scheduler_task.cancel()
                with suppress(asyncio.CancelledError):
                    await scheduler_task

    application = FastAPI(
        title="DearFuture API",
        description="Send a worry to the future and revisit it with real-world evidence.",
        version="1.0.0",
        lifespan=lifespan,
    )
    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @application.exception_handler(SQLAlchemyError)
    async def database_error_handler(_request, _exc):
        return JSONResponse(
            status_code=503,
            content={"detail": "The database is temporarily unavailable."},
        )

    @application.get("/", include_in_schema=False)
    def homepage():
        return FileResponse(STATIC_DIR / "index.html")

    @application.get("/q/{public_id}", include_in_schema=False)
    def question_page(public_id: str):
        return FileResponse(STATIC_DIR / "question.html")

    @application.get("/admin", include_in_schema=False)
    def admin_page():
        return FileResponse(STATIC_DIR / "admin.html")

    @application.get("/health")
    def health(db: Session = Depends(get_db)) -> dict:
        db.execute(text("SELECT 1"))
        settings = get_settings()
        return {
            "status": "ok",
            "database": "sqlite",
            "llm_configured": get_llm_client() is not None,
            "email_configured": bool(
                settings.mail_enabled
                and settings.mail_from
                and (settings.resend_api_key or settings.smtp_host)
            ),
            "scheduler_enabled": settings.scheduler_enabled,
        }

    @application.post("/api/questions", response_model=QuestionCreateResponse, status_code=201)
    def submit_question(payload: QuestionCreate, db: Session = Depends(get_db)):
        question = create_question(db, payload)
        safe_question = QuestionRead.model_validate(question)
        return QuestionCreateResponse(
            **safe_question.model_dump(),
            public_request_approved=question.is_public,
            message="Your question has been sent to the future.",
        )

    @application.get("/api/questions/{public_id}", response_model=QuestionRead)
    def read_public_question(public_id: str, db: Session = Depends(get_db)):
        question = get_public_question(db, public_id)
        if question is None:
            raise HTTPException(status_code=404, detail="Public question not found")
        return question

    @application.get("/api/public/questions", response_model=list[QuestionRead])
    def read_future_wall(
        limit: int = Query(default=24, ge=1, le=100),
        category: Optional[str] = Query(default=None, max_length=32),
        db: Session = Depends(get_db),
    ):
        return list_public_questions(db, limit=limit, category=category)

    @application.get("/api/public/stats", response_model=PublicStats)
    def read_public_stats(db: Session = Depends(get_db)):
        return get_public_stats(db)

    @application.get("/api/admin/questions", response_model=list[AdminQuestionRead])
    def read_admin_questions(
        status: Optional[str] = Query(default=None, max_length=32),
        authorization: Optional[str] = Header(default=None),
        db: Session = Depends(get_db),
    ):
        require_admin(authorization)
        return list_admin_questions(db, status=status)

    @application.delete("/api/admin/questions/{public_id}", response_model=AdminActionResponse)
    def delete_admin_question(
        public_id: str,
        authorization: Optional[str] = Header(default=None),
        db: Session = Depends(get_db),
    ):
        require_admin(authorization)
        question = soft_delete_question(db, public_id)
        if question is None:
            raise HTTPException(status_code=404, detail="Question not found")
        return AdminActionResponse(
            public_id=question.public_id,
            status=question.status,
            message="Question hidden from the public wall.",
        )

    @application.post(
        "/api/admin/questions/{public_id}/restore", response_model=AdminActionResponse
    )
    def restore_admin_question(
        public_id: str,
        authorization: Optional[str] = Header(default=None),
        db: Session = Depends(get_db),
    ):
        require_admin(authorization)
        question = restore_question(db, public_id)
        if question is None:
            raise HTTPException(status_code=404, detail="Question not found")
        return AdminActionResponse(
            public_id=question.public_id,
            status=question.status,
            message="Question restored.",
        )

    @application.post("/api/admin/questions/{public_id}/retry", response_model=AdminActionResponse)
    def retry_admin_question(
        public_id: str,
        background_tasks: BackgroundTasks,
        authorization: Optional[str] = Header(default=None),
        db: Session = Depends(get_db),
    ):
        require_admin(authorization)
        question = retry_question(db, public_id)
        if question is None:
            raise HTTPException(
                status_code=409,
                detail="Only unresolved, visible questions can be retried",
            )
        background_tasks.add_task(run_manual_retry, question.public_id)
        return AdminActionResponse(
            public_id=question.public_id,
            status=question.status,
            message="Question verification has started in the background.",
        )

    return application


app = create_app()
