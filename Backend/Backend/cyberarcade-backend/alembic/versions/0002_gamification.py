"""Add gamification tables and user XP/level columns

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users: add XP + level columns ────────────────────────────────────────
    op.execute("""
        ALTER TABLE users
            ADD COLUMN IF NOT EXISTS total_xp INTEGER NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS current_level INTEGER NOT NULL DEFAULT 1
    """)

    # ── levels ────────────────────────────────────────────────────────────────
    op.create_table(
        "levels",
        sa.Column("level_id", sa.Integer(), primary_key=True),
        sa.Column("min_xp", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(50), nullable=False),
    )
    op.create_index("ix_levels_min_xp", "levels", ["min_xp"])

    # ── xp_logs ───────────────────────────────────────────────────────────────
    op.create_table(
        "xp_logs",
        sa.Column("log_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(100), nullable=False),
        sa.Column("reference_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_xp_logs_user_id", "xp_logs", ["user_id"])
    op.create_index("ix_xp_logs_created_at", "xp_logs", ["created_at"])

    # ── badges ────────────────────────────────────────────────────────────────
    op.create_table(
        "badges",
        sa.Column("badge_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(60), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("icon", sa.String(10), nullable=False, server_default="🏆"),
        sa.Column("rarity", sa.String(20), nullable=False, server_default="common"),
        sa.Column("category", sa.String(40), nullable=False, server_default="general"),
        sa.Column("criteria", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("xp_reward", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_badges_slug", "badges", ["slug"])

    # ── user_badges ───────────────────────────────────────────────────────────
    op.create_table(
        "user_badges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("badge_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("badges.badge_id", ondelete="CASCADE"), nullable=False),
        sa.Column("awarded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("seen", sa.Boolean(), nullable=False, server_default="false"),
        sa.UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
    )
    op.create_index("ix_user_badges_user_id", "user_badges", ["user_id"])

    # ── user_streaks ──────────────────────────────────────────────────────────
    op.create_table(
        "user_streaks",
        sa.Column("streak_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.user_id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("current_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("longest_streak", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_active_date", sa.Date(), nullable=True),
        sa.Column("total_active_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_user_streaks_user_id", "user_streaks", ["user_id"])

    # ── activity_logs ─────────────────────────────────────────────────────────
    op.create_table(
        "activity_logs",
        sa.Column("log_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("activity_date", sa.Date(), nullable=False),
        sa.Column("activity_type", sa.String(30), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint("user_id", "activity_date", "activity_type", name="uq_user_activity"),
    )
    op.create_index("ix_activity_logs_user_date", "activity_logs", ["user_id", "activity_date"])


def downgrade() -> None:
    op.drop_table("activity_logs")
    op.drop_table("user_streaks")
    op.drop_table("user_badges")
    op.drop_table("badges")
    op.drop_table("xp_logs")
    op.drop_table("levels")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS total_xp, DROP COLUMN IF EXISTS current_level")
