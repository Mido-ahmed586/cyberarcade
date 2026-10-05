"""
Subscription + payment-checkout routes.

The flow is built to mirror real payment providers (Stripe / Paymob / Fawry /
PayPal). When you swap in a real provider, only TWO things need to change:

  1. `_create_provider_checkout_url(...)` — call the provider's SDK to create a
     real checkout session and return its hosted URL.
  2. `_verify_provider_payment(...)` — verify the payment server-side (either
     by polling the provider API or, much better, via a webhook with a
     signature check).

Everything around that — the database lifecycle, the redirect handling, the
frontend integration — stays exactly as is.

WHY A "MOCK" PAGE INSTEAD OF JUST CALLING THE PROVIDER?
  Because building the full flow with a real provider requires:
    - A provider account (Stripe/Paymob/etc.) with API keys
    - Webhook signature secrets
    - A publicly-reachable HTTPS endpoint for the webhook (impossible from
      localhost without ngrok/cloudflared)
    - Decisions about pricing, currency, billing cycles
  The mock page lets the entire UX work end-to-end on localhost so you can
  ship the integration when you have those details. The mock is intentionally
  obvious — it has a "DEMO MODE" banner and won't be mistaken for production.
"""

import secrets
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.subscription import (
    CheckoutCreateRequest,
    CheckoutCreateResponse,
    CheckoutSessionInfo,
    PlanInfo,
    SubscriptionCreateRequest,
    SubscriptionResponse,
)

router = APIRouter(prefix="/api/subscriptions", tags=["Subscriptions"])


# ---------------------------------------------------------------------------
# Plan catalogue
# ---------------------------------------------------------------------------
PLAN_PRICES = {
    "premium": {"amount_cents": 1900, "currency": "USD", "duration_days": 30},
}

CHECKOUT_SESSION_TTL_MINUTES = 30


# ---------------------------------------------------------------------------
# Provider hooks — replace these two functions with a real provider integration
# ---------------------------------------------------------------------------
def _create_provider_checkout_url(session_id: str, plan: str, amount_cents: int,
                                  currency: str, success_url: str, cancel_url: str) -> str:
    """
    PROVIDER HOOK #1.

    For now this returns a URL on our own backend that serves a sandbox
    payment page. To integrate Stripe:

        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        s = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": currency.lower(),
                    "product_data": {"name": f"CyberArcade {plan}"},
                    "unit_amount": amount_cents,
                },
                "quantity": 1,
            }],
            mode="subscription",
            success_url=success_url + "&provider_ref={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            client_reference_id=session_id,
        )
        return s.url

    For Paymob (Egypt), the equivalent involves /auth/tokens, then
    /ecommerce/orders, then /acceptance/payment_keys, then redirect to the
    iframe URL. See https://docs.paymob.com/docs/accept-standard-redirect.
    """
    # Mock provider: route the user to OUR backend's hosted sandbox page.
    return f"{settings.BACKEND_PUBLIC_URL}/api/subscriptions/sandbox/{session_id}"


def _verify_provider_payment(subscription: Subscription) -> bool:
    """
    PROVIDER HOOK #2.

    This is called when the provider redirects the user back. With a real
    provider you should NOT trust the redirect alone — always verify with the
    provider's API or rely on a webhook (recommended).

    For Stripe:
        s = stripe.checkout.Session.retrieve(subscription.payment_session_id)
        return s.payment_status == "paid"

    The mock provider trusts our own /complete endpoint and is already
    verified by the time this is called.
    """
    return subscription.status == "active"


# ---------------------------------------------------------------------------
# Standard subscription endpoints
# ---------------------------------------------------------------------------
@router.get("/plans", response_model=list[PlanInfo])
async def list_plans():
    return [
        PlanInfo(
            id="free", name="Free", price="$0", period="forever",
            features=[
                "Access to first 2 labs per course",
                "Community support",
                "Basic AI assistant",
                "Progress tracking",
            ],
        ),
        PlanInfo(
            id="premium", name="Premium", price="$19", period="/month",
            features=[
                "Unlimited access to ALL labs",
                "All courses & advanced modules",
                "Priority AI assistant",
                "Join instructor-led classes",
                "Auto-solve on all labs",
                "Priority support",
                "Certificate of completion",
            ],
        ),
    ]


@router.get("/me", response_model=SubscriptionResponse)
async def get_my_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Subscription)
        .where(
            Subscription.user_id == current_user.user_id,
            Subscription.status == "active",
        )
        .order_by(Subscription.created_at.desc())
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription found")
    return sub


@router.post("", response_model=SubscriptionResponse, status_code=201)
async def subscribe(
    req: SubscriptionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Free-only fast path. Premium MUST go through /checkout — we reject it
    here so the frontend can't bypass the payment step.
    """
    if req.plan == "premium":
        raise HTTPException(
            status_code=400,
            detail="Premium subscriptions must go through /checkout",
        )

    # Cancel any existing active subs
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == current_user.user_id,
            Subscription.status == "active",
        )
    )
    for s in result.scalars().all():
        s.status = "cancelled"

    today = date.today()
    new_sub = Subscription(
        user_id=current_user.user_id,
        plan="free",
        status="active",
        start_date=today,
        end_date=today + timedelta(days=36500),  # ~100y for the free tier
    )
    db.add(new_sub)
    await db.flush()
    await db.refresh(new_sub)
    return new_sub


# ---------------------------------------------------------------------------
# Checkout flow
# ---------------------------------------------------------------------------
@router.post("/checkout", response_model=CheckoutCreateResponse, status_code=201)
async def create_checkout(
    req: CheckoutCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Step 1 of the payment flow.

    Creates a `pending` subscription row tied to a unique session_id, then
    asks the provider for a hosted-checkout URL the user should be redirected
    to. The frontend should `window.location = checkout_url` — DO NOT try to
    iframe it; real providers block that.
    """
    plan = req.plan
    if plan not in PLAN_PRICES:
        raise HTTPException(status_code=400, detail=f"Plan '{plan}' is not purchasable")

    pricing = PLAN_PRICES[plan]
    session_id = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=CHECKOUT_SESSION_TTL_MINUTES)

    today = date.today()
    pending = Subscription(
        user_id=current_user.user_id,
        plan=plan,
        status="pending",
        start_date=today,
        end_date=today + timedelta(days=pricing["duration_days"]),
        payment_provider="mock",
        payment_session_id=session_id,
        amount_cents=pricing["amount_cents"],
        currency=pricing["currency"],
    )
    db.add(pending)
    await db.flush()

    # The frontend will receive these as ?payment=success or ?payment=cancelled
    # at its root and surface a toast.
    success_url = f"{settings.FRONTEND_URL}/?payment=success&session={session_id}"
    cancel_url = f"{settings.FRONTEND_URL}/?payment=cancelled&session={session_id}"

    checkout_url = _create_provider_checkout_url(
        session_id=session_id,
        plan=plan,
        amount_cents=pricing["amount_cents"],
        currency=pricing["currency"],
        success_url=success_url,
        cancel_url=cancel_url,
    )

    return CheckoutCreateResponse(
        session_id=session_id,
        checkout_url=checkout_url,
        expires_at=expires_at,
        amount_cents=pricing["amount_cents"],
        currency=pricing["currency"],
        plan=plan,
    )


@router.get("/checkout/{session_id}", response_model=CheckoutSessionInfo)
async def get_checkout_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Read-only endpoint used by the mock payment page. Public on purpose — the
    session_id is a high-entropy random token, equivalent to a Stripe session
    ID. Real providers don't gate this either; the page is meant to be
    visited un-authenticated by the user's browser after redirect.
    """
    result = await db.execute(
        select(Subscription, User)
        .join(User, User.user_id == Subscription.user_id)
        .where(Subscription.payment_session_id == session_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Checkout session not found")
    sub, user = row

    return CheckoutSessionInfo(
        session_id=session_id,
        plan=sub.plan,
        amount_cents=sub.amount_cents or 0,
        currency=sub.currency or "USD",
        status=sub.status,
        user_email=user.email,
        expires_at=sub.created_at + timedelta(minutes=CHECKOUT_SESSION_TTL_MINUTES),
        success_url=f"{settings.FRONTEND_URL}/?payment=success&session={session_id}",
        cancel_url=f"{settings.FRONTEND_URL}/?payment=cancelled&session={session_id}",
    )


@router.post("/checkout/{session_id}/complete", response_model=SubscriptionResponse)
async def complete_checkout(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Mark a pending subscription as active. Called by the mock page when the
    user clicks "Pay". With a real provider this is replaced by a webhook
    (`/webhooks/stripe` or similar) that verifies the signature.
    """
    result = await db.execute(
        select(Subscription).where(Subscription.payment_session_id == session_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Session not found")
    if sub.status == "active":
        return sub  # idempotent
    if sub.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot complete a '{sub.status}' session",
        )

    # Deactivate previous active subs for this user
    prev = await db.execute(
        select(Subscription).where(
            Subscription.user_id == sub.user_id,
            Subscription.status == "active",
            Subscription.subscription_id != sub.subscription_id,
        )
    )
    for s in prev.scalars().all():
        s.status = "cancelled"

    sub.status = "active"
    sub.payment_reference = f"mock_{secrets.token_hex(8)}"
    await db.flush()
    await db.refresh(sub)
    return sub


@router.post("/checkout/{session_id}/cancel", response_model=SubscriptionResponse)
async def cancel_checkout(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Subscription).where(Subscription.payment_session_id == session_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Session not found")
    if sub.status == "pending":
        sub.status = "cancelled"
        await db.flush()
        await db.refresh(sub)
    return sub


# ---------------------------------------------------------------------------
# Mock provider's hosted page (HTML).
#
# This is the page the user is redirected to after creating a checkout
# session. Replace this whole endpoint by deleting it once a real provider is
# wired in — at that point _create_provider_checkout_url returns the
# provider's URL instead of one on our backend.
# ---------------------------------------------------------------------------
from fastapi.responses import HTMLResponse  # noqa: E402

@router.get("/sandbox/{session_id}", include_in_schema=False, response_class=HTMLResponse)
async def mock_payment_page(session_id: str):
    """Self-contained sandbox payment page. No assets, no JS frameworks."""
    api_base = settings.BACKEND_PUBLIC_URL
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>CyberArcade — Sandbox Payment</title>
<meta name="viewport" content="width=device-width,initial-scale=1" />
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; background: #0b0f17; color: #e8edf5; margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 24px; }}
  .card {{ background: #131826; border: 1px solid #232b3d; border-radius: 14px; padding: 32px; max-width: 440px; width: 100%; box-shadow: 0 20px 50px rgba(0,0,0,.5); }}
  .demo {{ background: #f59e0b; color: #000; font-weight: 700; font-size: 11px; letter-spacing: 1px; padding: 6px 10px; border-radius: 6px; display: inline-block; margin-bottom: 18px; }}
  h1 {{ margin: 0 0 6px; font-size: 22px; }}
  .sub {{ color: #94a3b8; font-size: 14px; margin-bottom: 24px; }}
  .row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #232b3d; font-size: 14px; }}
  .row:last-child {{ border-bottom: none; font-size: 18px; font-weight: 700; padding-top: 14px; }}
  .row span:first-child {{ color: #94a3b8; }}
  .form {{ margin: 22px 0; display: flex; flex-direction: column; gap: 10px; }}
  .form label {{ font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: .8px; }}
  .form input {{ background: #0b0f17; border: 1px solid #232b3d; color: #e8edf5; padding: 10px 12px; border-radius: 8px; font-size: 14px; font-family: inherit; }}
  .form input:focus {{ outline: none; border-color: #00f0ff; }}
  .actions {{ display: flex; gap: 10px; margin-top: 22px; }}
  button {{ flex: 1; padding: 12px; border-radius: 8px; border: none; font-size: 14px; font-weight: 600; cursor: pointer; transition: .15s; font-family: inherit; }}
  .pay {{ background: #00f0ff; color: #000; }}
  .pay:hover {{ background: #4df5ff; }}
  .pay:disabled {{ opacity: .5; cursor: not-allowed; }}
  .cancel {{ background: transparent; border: 1px solid #232b3d; color: #94a3b8; }}
  .cancel:hover {{ border-color: #94a3b8; color: #e8edf5; }}
  .err {{ color: #fb7185; font-size: 13px; margin-top: 12px; min-height: 16px; }}
  .ok {{ color: #4ade80; font-size: 13px; margin-top: 12px; }}
  .small {{ color: #64748b; font-size: 11px; text-align: center; margin-top: 18px; }}
</style>
</head>
<body>
  <div class="card">
    <div class="demo">DEMO MODE — NO REAL CHARGE</div>
    <h1>CyberArcade Checkout</h1>
    <p class="sub">Sandbox payment page (mock provider)</p>
    <div id="info">Loading session...</div>
    <div class="form">
      <label>Card number</label>
      <input id="card" placeholder="4242 4242 4242 4242" value="4242 4242 4242 4242" />
      <label>Expiry / CVC</label>
      <input id="exp" placeholder="12/34   123" value="12/34   123" />
    </div>
    <div class="actions">
      <button class="cancel" id="cancelBtn">Cancel</button>
      <button class="pay" id="payBtn">Pay</button>
    </div>
    <div class="err" id="msg"></div>
    <p class="small">When you wire in Stripe / Paymob, delete this page — the user will be redirected straight to the provider instead.</p>
  </div>
<script>
  const SESSION_ID = {session_id!r};
  const API = {api_base!r};
  const info = document.getElementById('info');
  const msg = document.getElementById('msg');
  const payBtn = document.getElementById('payBtn');
  const cancelBtn = document.getElementById('cancelBtn');
  let session = null;

  fetch(API + '/api/subscriptions/checkout/' + SESSION_ID)
    .then(r => r.ok ? r.json() : Promise.reject(r))
    .then(s => {{
      session = s;
      info.innerHTML =
        '<div class="row"><span>Plan</span><span>' + s.plan.toUpperCase() + '</span></div>' +
        '<div class="row"><span>Email</span><span>' + s.user_email + '</span></div>' +
        '<div class="row"><span>Status</span><span>' + s.status + '</span></div>' +
        '<div class="row"><span>Total</span><span>' + (s.amount_cents/100).toFixed(2) + ' ' + s.currency + '</span></div>';
      if (s.status !== 'pending') {{
        payBtn.disabled = true; cancelBtn.disabled = true;
        msg.textContent = 'This session is already ' + s.status + '.';
      }}
    }})
    .catch(() => {{
      info.textContent = 'Session not found or expired.';
      payBtn.disabled = true; cancelBtn.disabled = true;
    }});

  payBtn.onclick = async () => {{
    payBtn.disabled = true; cancelBtn.disabled = true;
    msg.textContent = 'Processing...';
    try {{
      const r = await fetch(API + '/api/subscriptions/checkout/' + SESSION_ID + '/complete', {{ method: 'POST' }});
      if (!r.ok) throw new Error('Payment failed');
      msg.className = 'ok'; msg.textContent = 'Payment successful! Redirecting...';
      setTimeout(() => window.location = session.success_url, 800);
    }} catch (e) {{
      msg.textContent = e.message || 'Payment failed';
      payBtn.disabled = false; cancelBtn.disabled = false;
    }}
  }};

  cancelBtn.onclick = async () => {{
    payBtn.disabled = true; cancelBtn.disabled = true;
    try {{
      await fetch(API + '/api/subscriptions/checkout/' + SESSION_ID + '/cancel', {{ method: 'POST' }});
    }} finally {{
      window.location = session ? session.cancel_url : {settings.FRONTEND_URL!r};
    }}
  }};
</script>
</body>
</html>"""
    return HTMLResponse(html)
