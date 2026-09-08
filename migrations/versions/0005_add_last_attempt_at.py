"""Track the last verification attempt for admin diagnostics.

Revision ID: 0005_add_last_attempt_at
Revises: 0004_add_intake_record
Create Date: 2026-09-08
"""

import sqlalchemy as sa
from alembic import op

revision = "0005_add_last_attempt_at"
down_revision = "0004_add_intake_record"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("questions", "last_attempt_at")
