"""Allow letters without an email address.

Revision ID: 0002_make_email_optional
Revises: 0001_create_questions
Create Date: 2026-09-05
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_make_email_optional"
down_revision = "0001_create_questions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("questions") as batch_op:
        batch_op.alter_column(
            "email",
            existing_type=sa.String(length=320),
            nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("questions") as batch_op:
        batch_op.alter_column(
            "email",
            existing_type=sa.String(length=320),
            nullable=False,
        )
