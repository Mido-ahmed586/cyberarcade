import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="student")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    lab_instances = relationship("LabInstance", back_populates="user", cascade="all, delete-orphan")
    lab_progress = relationship("LabProgress", back_populates="user", cascade="all, delete-orphan")
    chatbot_messages = relationship("ChatbotConversation", back_populates="user", cascade="all, delete-orphan")
    enrollments = relationship("ClassEnrollment", back_populates="student", cascade="all, delete-orphan")
    taught_classes = relationship("Class", back_populates="instructor")
    xp_logs = relationship("XPLog", back_populates="user", cascade="all, delete-orphan")
    user_badges = relationship("UserBadge", back_populates="user", cascade="all, delete-orphan")
    streak = relationship("UserStreak", back_populates="user", uselist=False, cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")
