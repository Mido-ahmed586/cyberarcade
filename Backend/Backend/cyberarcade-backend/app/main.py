from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import inspect, text

from app.core.config import settings
from app.core.database import engine, Base

# Import all models so they are registered with SQLAlchemy
import app.models  # noqa: F401

# Import routers
from app.routers import (
    auth,
    courses,
    labs,
    classes,
    admin,
    chatbot,
    subscription,
    autosolve,
    certificates,
    ai_coach,
    gamification,
)


def _ensure_extra_columns(sync_conn):
    """Add any columns that were added after the initial schema was created."""
    inspector = inspect(sync_conn)

    if "lab_tasks" in inspector.get_table_names():
        existing = {col["name"] for col in inspector.get_columns("lab_tasks")}
        if "autosolve_commands" not in existing:
            sync_conn.execute(
                text("ALTER TABLE lab_tasks ADD COLUMN autosolve_commands JSONB DEFAULT '[]'::jsonb NOT NULL")
            )

    if "lab_progress" in inspector.get_table_names():
        existing = {col["name"] for col in inspector.get_columns("lab_progress")}
        if "attempt_count" not in existing:
            sync_conn.execute(
                text("ALTER TABLE lab_progress ADD COLUMN attempt_count INTEGER DEFAULT 0 NOT NULL")
            )

    # Gamification columns on users
    if "users" in inspector.get_table_names():
        existing = {col["name"] for col in inspector.get_columns("users")}
        if "total_xp" not in existing:
            sync_conn.execute(text("ALTER TABLE users ADD COLUMN total_xp INTEGER DEFAULT 0 NOT NULL"))
        if "current_level" not in existing:
            sync_conn.execute(text("ALTER TABLE users ADD COLUMN current_level INTEGER DEFAULT 1 NOT NULL"))


def _ensure_subscription_columns(sync_conn):
    inspector = inspect(sync_conn)
    if "subscriptions" not in inspector.get_table_names():
        return

    existing_columns = {col["name"] for col in inspector.get_columns("subscriptions")}
    if "payment_provider" not in existing_columns:
        sync_conn.execute(text("ALTER TABLE subscriptions ADD COLUMN payment_provider VARCHAR(30)"))
    if "payment_session_id" not in existing_columns:
        sync_conn.execute(text("ALTER TABLE subscriptions ADD COLUMN payment_session_id VARCHAR(64)"))
    if "payment_reference" not in existing_columns:
        sync_conn.execute(text("ALTER TABLE subscriptions ADD COLUMN payment_reference VARCHAR(255)"))
    if "amount_cents" not in existing_columns:
        sync_conn.execute(text("ALTER TABLE subscriptions ADD COLUMN amount_cents INTEGER"))
    if "currency" not in existing_columns:
        sync_conn.execute(text("ALTER TABLE subscriptions ADD COLUMN currency VARCHAR(3)"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    if settings.DEBUG:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.run_sync(_ensure_extra_columns)
            await conn.run_sync(_ensure_subscription_columns)
        print("Database tables created (dev mode)")

    yield

    await engine.dispose()
    print("Database connection closed")


app = FastAPI(
    title=settings.APP_NAME,
    description="CyberArcade — An Educational Cybersecurity Training Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(labs.router)
app.include_router(classes.router)
app.include_router(admin.router)
app.include_router(chatbot.router)
app.include_router(subscription.router)
app.include_router(autosolve.router)
app.include_router(certificates.router)
app.include_router(ai_coach.router)
app.include_router(gamification.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "running",
        "app": settings.APP_NAME,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}
