import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Lab(Base):
    __tablename__ = "labs"

    lab_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False
    )
    module_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("modules.module_id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    docker_compose_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    has_auto_solve: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    max_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=120)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    course = relationship("Course", back_populates="labs")
    module = relationship("Module", back_populates="labs")
    tasks = relationship("LabTask", back_populates="lab", cascade="all, delete-orphan",
                         order_by="LabTask.sort_order")
    instances = relationship("LabInstance", back_populates="lab", cascade="all, delete-orphan")
    progress = relationship("LabProgress", back_populates="lab", cascade="all, delete-orphan")


class LabTask(Base):
    __tablename__ = "lab_tasks"

    task_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    lab_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("labs.lab_id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    expected_answer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    autosolve_commands: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    lab = relationship("Lab", back_populates="tasks")
    hints = relationship("Hint", back_populates="task", cascade="all, delete-orphan",
                         order_by="Hint.hint_order")
    progress = relationship("LabProgress", back_populates="task", cascade="all, delete-orphan")


class Hint(Base):
    __tablename__ = "hints"

    hint_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lab_tasks.task_id", ondelete="CASCADE"), nullable=False
    )
    hint_text: Mapped[str] = mapped_column(Text, nullable=False)
    hint_order: Mapped[int] = mapped_column(Integer, nullable=False)
    delay_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    task = relationship("LabTask", back_populates="hints")
