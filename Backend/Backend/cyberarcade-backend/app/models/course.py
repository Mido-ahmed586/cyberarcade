import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, Numeric, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"

    course_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty_level: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    estimated_hours: Mapped[float | None] = mapped_column(Numeric(4, 1), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan",
                           order_by="Module.sort_order")
    labs = relationship("Lab", back_populates="course", cascade="all, delete-orphan",
                        order_by="Lab.sort_order")
    classes = relationship("Class", back_populates="course")


class Module(Base):
    __tablename__ = "modules"

    module_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    course = relationship("Course", back_populates="modules")
    labs = relationship("Lab", back_populates="module")
