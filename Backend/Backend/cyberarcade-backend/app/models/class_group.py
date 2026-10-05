import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Integer, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Class(Base):
    __tablename__ = "classes"

    class_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    class_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    instructor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.course_id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_students: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    instructor = relationship("User", back_populates="taught_classes")
    course = relationship("Course", back_populates="classes")
    enrollments = relationship("ClassEnrollment", back_populates="class_group",
                               cascade="all, delete-orphan")


class ClassEnrollment(Base):
    __tablename__ = "class_enrollments"
    __table_args__ = (
        UniqueConstraint("class_id", "student_id", name="uq_class_student"),
    )

    enrollment_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    class_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("classes.class_id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    class_group = relationship("Class", back_populates="enrollments")
    student = relationship("User", back_populates="enrollments")
