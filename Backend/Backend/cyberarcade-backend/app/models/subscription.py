import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    subscription_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    plan: Mapped[str] = mapped_column(String(30), nullable=False)
    # status: pending | active | cancelled | failed
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    start_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # --- Payment fields -----------------------------------------------------
    # Provider name: "mock", "stripe", "paymob", etc. The mock provider is
    # used until a real one is wired in.
    payment_provider: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # Unique session ID we hand back to the frontend for the redirect URL.
    payment_session_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    # External transaction ID returned by the provider after success.
    payment_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Amount charged in cents (avoids float math).
    amount_cents: Mapped[int | None] = mapped_column(nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True, default="USD")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User", back_populates="subscriptions")
