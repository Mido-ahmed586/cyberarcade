from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date, datetime
from typing import Optional


# -------------------------------------------------------------------------
# Existing schemas
# -------------------------------------------------------------------------
class SubscriptionCreateRequest(BaseModel):
    """Used by /api/subscriptions for the free downgrade path only.
    Premium subscriptions go through /checkout."""
    plan: str = Field(..., pattern="^(free|premium)$")


class SubscriptionResponse(BaseModel):
    subscription_id: UUID
    user_id: UUID
    plan: str
    status: str
    start_date: date
    end_date: date
    payment_reference: Optional[str] = None
    payment_provider: Optional[str] = None
    payment_session_id: Optional[str] = None
    amount_cents: Optional[int] = None
    currency: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PlanInfo(BaseModel):
    id: str
    name: str
    price: str
    period: str
    features: list[str]


# -------------------------------------------------------------------------
# Checkout / payment flow
# -------------------------------------------------------------------------
class CheckoutCreateRequest(BaseModel):
    """Frontend asks the backend to create a checkout session."""
    plan: str = Field(..., pattern="^(premium)$")  # only premium needs checkout


class CheckoutCreateResponse(BaseModel):
    """Backend returns a redirect URL for the frontend to send the user to."""
    session_id: str
    checkout_url: str
    expires_at: datetime
    amount_cents: int
    currency: str
    plan: str


class CheckoutSessionInfo(BaseModel):
    """Detail shown on the mock payment page."""
    session_id: str
    plan: str
    amount_cents: int
    currency: str
    status: str  # pending | active | cancelled | failed
    user_email: str
    expires_at: datetime
    success_url: str
    cancel_url: str
