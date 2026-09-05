"""Create the DearFuture product schema.

Revision ID: 0001_create_questions
Revises:
Create Date: 2026-09-05
"""

import sqlalchemy as sa
from alembic import op

revision = "0001_create_questions"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("claim", sa.Text(), nullable=False),
        sa.Column("verification_criteria", sa.JSON(), nullable=False),
        sa.Column("verification_plan", sa.Text(), nullable=False),
        sa.Column("check_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("public_requested", sa.Boolean(), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("model_used", sa.Boolean(), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=True),
        sa.Column("verification_summary", sa.Text(), nullable=True),
        sa.Column("future_letter", sa.Text(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_questions_public_id", "questions", ["public_id"], unique=True)
    op.create_index("ix_questions_check_at", "questions", ["check_at"], unique=False)
    op.create_index("ix_questions_status", "questions", ["status"], unique=False)
    op.create_index(
        "ix_questions_public_status", "questions", ["is_public", "status"], unique=False
    )

    op.create_table(
        "evidence",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "retrieved_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evidence_question_id", "evidence", ["question_id"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_question_id", "notifications", ["question_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_notifications_question_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_evidence_question_id", table_name="evidence")
    op.drop_table("evidence")
    op.drop_index("ix_questions_public_status", table_name="questions")
    op.drop_index("ix_questions_status", table_name="questions")
    op.drop_index("ix_questions_check_at", table_name="questions")
    op.drop_index("ix_questions_public_id", table_name="questions")
    op.drop_table("questions")
