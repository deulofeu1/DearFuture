"""Store the structured intake decision for admin diagnostics.

Revision ID: 0004_add_intake_record
Revises: 0003_add_soft_delete
Create Date: 2026-09-06
"""

import sqlalchemy as sa
from alembic import op

revision = "0004_add_intake_record"
down_revision = "0003_add_soft_delete"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("intake_record", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("questions", "intake_record")
