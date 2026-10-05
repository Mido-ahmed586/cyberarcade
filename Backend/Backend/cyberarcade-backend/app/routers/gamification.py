from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services import gamification_service as gs

router = APIRouter(prefix="/api/gamification", tags=["Gamification"])


@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await gs.get_profile(db, current_user.user_id)


@router.get("/badges")
async def get_all_badges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await gs.get_all_badges(db, current_user.user_id)


@router.post("/badges/seen")
async def mark_badges_seen(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await gs.mark_badges_seen(db, current_user.user_id)
    return {"ok": True}


@router.get("/streak")
async def get_streak(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await gs.get_profile(db, current_user.user_id)
    return profile.get("streak", {})


@router.get("/xp-history")
async def get_xp_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await gs.get_xp_history(db, current_user.user_id, limit=limit)


@router.get("/activity")
async def get_activity(
    days: int = Query(90, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await gs.get_activity_heatmap(db, current_user.user_id, days=days)


@router.get("/leaderboard")
async def get_leaderboard(
    limit: int = Query(50, ge=5, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await gs.get_leaderboard(db, limit=limit, current_user_id=current_user.user_id)


@router.get("/dashboard")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aggregated dashboard data including gamification + course progress."""
    from sqlalchemy import select, func
    from app.models.lab_instance import LabProgress
    from app.models.lab import Lab

    profile = await gs.get_profile(db, current_user.user_id)

    # Recent XP history
    xp_history = await gs.get_xp_history(db, current_user.user_id, limit=10)

    # Activity heatmap (last 90 days)
    activity = await gs.get_activity_heatmap(db, current_user.user_id, days=90)

    return {
        **profile,
        "xp_history": xp_history,
        "activity": activity,
    }
