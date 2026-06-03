import os
import datetime
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.models.user import User, Subscription
from app.api.auth import get_current_user

try:
    import stripe as stripe_module
    stripe = stripe_module
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
    HAS_STRIPE = True
except ImportError:
    HAS_STRIPE = False

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])

PLANS = {
    "free": {"name": "Free", "predictions_per_month": 10, "dft_credits": 0, "price_monthly": 0},
    "pro": {"name": "Pro", "predictions_per_month": 500, "dft_credits": 50, "price_monthly": 49},
    "team": {"name": "Team", "predictions_per_month": 5000, "dft_credits": 500, "price_monthly": 199},
}


class CreateCheckoutSession(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str


@router.get("/plans")
def list_plans():
    return PLANS


@router.post("/create-checkout-session")
def create_checkout(data: CreateCheckoutSession, current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    if not HAS_STRIPE or not stripe.api_key:
        raise HTTPException(status_code=400, detail="Stripe not configured")

    session = stripe.checkout.Session.create(
        customer_email=current_user.email,
        payment_method_types=["card"],
        line_items=[{"price": data.price_id, "quantity": 1}],
        mode="subscription",
        success_url=data.success_url,
        cancel_url=data.cancel_url,
        metadata={"user_id": current_user.id},
    )
    return {"session_id": session.id, "url": session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request):
    if not HAS_STRIPE or not stripe.api_key:
        return {"status": "ignored"}

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = int(session["metadata"]["user_id"])

        db = SessionLocal()
        sub = Subscription(
            user_id=user_id,
            tier="pro",
            stripe_subscription_id=session["subscription"],
            status="active",
            current_period_start=datetime.datetime.utcfromtimestamp(session.get("created", 0)),
            current_period_end=datetime.datetime.utcfromtimestamp(session.get("expires_at", 0) or 0),
        )
        db.add(sub)
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.subscription_tier = "pro"
        db.commit()
        db.close()

    return {"status": "received"}
