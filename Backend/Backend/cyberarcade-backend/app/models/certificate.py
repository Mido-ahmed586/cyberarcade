import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Certificate(Base):
    __tablename__ = "certificates"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_user_course_cert"),
    )

    certificate_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    serial_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False
    )
    student_name: Mapped[str] = mapped_column(String(120), nullable=False)
    course_name: Mapped[str] = mapped_column(String(200), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    pdf_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(20), nullable=False, default="valid")

    user = relationship("User", backref="certificates")
    course = relationship("Course", backref="certificates")
