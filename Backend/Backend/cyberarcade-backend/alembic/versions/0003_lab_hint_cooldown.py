"""Add lab_hint_cooldowns table for global per-lab hint cooldown

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-28
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lab_hint_cooldowns",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("lab_id", sa.UUID(), nullable=False),
        sa.Column("last_hint_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lab_id"], ["labs.lab_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "lab_id"),
    )


def downgrade() -> None:
    op.drop_table("lab_hint_cooldowns")
