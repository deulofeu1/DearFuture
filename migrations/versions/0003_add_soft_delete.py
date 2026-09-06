"""Add soft deletion fields for admin moderation.

Revision ID: 0003_add_soft_delete
Revises: 0002_make_email_optional
Create Date: 2026-09-06
"""

import sqlalchemy as sa
from alembic import op


revision = "0003_add_soft_delete"
down_revision = "0002_make_email_optional"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("questions", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_questions_is_deleted", "questions", ["is_deleted"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_questions_is_deleted", table_name="questions")
    op.drop_column("questions", "deleted_at")
    op.drop_column("questions", "is_deleted")
