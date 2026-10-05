import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserLearningMetric(Base):
    """Aggregated learning behavior snapshot used by the AI Coach."""

    __tablename__ = "user_learning_metrics"

    metric_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    completed_tasks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_task_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hints_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    time_spent_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    labs_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    course_progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chatbot_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class UserSkillScore(Base):
    """Per-user score for a broad cybersecurity skill category."""

    __tablename__ = "user_skill_scores"
    __table_args__ = (UniqueConstraint("user_id", "skill_category", name="uq_user_skill_category"),)

    score_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_category: Mapped[str] = mapped_column(String(80), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evidence: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class UserAIInsight(Base):
    """Stored AI/rule-based performance insight shown in the AI Coach page."""

    __tablename__ = "user_ai_insights"

    insight_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    strengths: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    weaknesses: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    improvement_plan: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    recommended_labs: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    generated_by: Mapped[str] = mapped_column(String(30), nullable=False, default="rules")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
