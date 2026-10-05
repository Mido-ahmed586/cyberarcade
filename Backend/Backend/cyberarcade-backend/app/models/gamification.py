import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, Boolean, Integer, Text, DateTime, Date, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Level(Base):
    __tablename__ = "levels"

    level_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    min_xp: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(50), nullable=False)


class XPLog(Base):
    __tablename__ = "xp_logs"

    log_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    reference_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User", back_populates="xp_logs")


class Badge(Base):
    __tablename__ = "badges"

    badge_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[str] = mapped_column(String(10), nullable=False, default="🏆")
    rarity: Mapped[str] = mapped_column(String(20), nullable=False, default="common")
    category: Mapped[str] = mapped_column(String(40), nullable=False, default="general")
    criteria: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user_badges = relationship("UserBadge", back_populates="badge", cascade="all, delete-orphan")


class UserBadge(Base):
    __tablename__ = "user_badges"
    __table_args__ = (
        UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True
    )
    badge_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("badges.badge_id", ondelete="CASCADE"), nullable=False
    )
    awarded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    seen: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="user_badges")
    badge = relationship("Badge", back_populates="user_badges")


class UserStreak(Base):
    __tablename__ = "user_streaks"

    streak_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    current_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_active_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_active_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User", back_populates="streak")


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    __table_args__ = (
        UniqueConstraint("user_id", "activity_date", "activity_type", name="uq_user_activity"),
        Index("ix_activity_logs_user_date", "user_id", "activity_date"),
    )

    log_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    activity_date: Mapped[date] = mapped_column(Date, nullable=False)
    activity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    user = relationship("User", back_populates="activity_logs")
