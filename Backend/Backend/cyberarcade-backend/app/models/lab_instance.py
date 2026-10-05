import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, UniqueConstraint, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class LabInstance(Base):
    __tablename__ = "lab_instances"

    instance_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    lab_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("labs.lab_id", ondelete="CASCADE"), nullable=False
    )
    container_ids: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    guacamole_connection_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="starting")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    terminated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="lab_instances")
    lab = relationship("Lab", back_populates="instances")


class LabProgress(Base):
    __tablename__ = "lab_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "lab_id", "task_id", name="uq_user_lab_task"),
    )

    progress_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    lab_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("labs.lab_id", ondelete="CASCADE"), nullable=False
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lab_tasks.task_id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="not_started")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hints_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_hint_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_answer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    auto_solve_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="lab_progress")
    lab = relationship("Lab", back_populates="progress")
    task = relationship("LabTask", back_populates="progress")


class LabHintCooldown(Base):
    """Global per-user-per-lab hint cooldown. One row tracks the last time this
    user opened any hint in this lab, enforcing a single shared 30-second window
    across all tasks."""
    __tablename__ = "lab_hint_cooldowns"
    __table_args__ = (PrimaryKeyConstraint("user_id", "lab_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    lab_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("labs.lab_id", ondelete="CASCADE"), nullable=False
    )
    last_hint_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
