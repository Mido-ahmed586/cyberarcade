"""
Gamification service — XP, levels, badges, streaks, leaderboard.

All public functions are safe to call inside an existing DB session.
They call db.flush() but NOT db.commit() so they participate in the
caller's transaction (the commit belongs to the router/endpoint).
"""

import uuid
from datetime import datetime, date, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.lab import Lab, LabTask
from app.models.lab_instance import LabProgress
from app.models.course import Course
from app.models.gamification import Level, XPLog, Badge, UserBadge, UserStreak, ActivityLog

# ─── XP reward values ─────────────────────────────────────────────────────────
XP_TASK_COMPLETE = 15
XP_TASK_AUTO_SOLVED = 10
XP_FIRST_TRY_BONUS = 10
XP_NO_HINTS_BONUS = 5
XP_LAB_COMPLETE = 50
XP_COURSE_COMPLETE = 200
XP_STREAK_7 = 50
XP_STREAK_30 = 200


# ─── Public API ───────────────────────────────────────────────────────────────

async def on_task_complete(
    db: AsyncSession,
    user_id,
    task_id,
    progress: LabProgress,
) -> dict:
    """
    Called after a task is successfully completed (correct answer or auto-solve).
    Returns reward summary dict safe for JSON serialisation.
    """
    uid = uuid.UUID(str(user_id))

    user_res = await db.execute(select(User).where(User.user_id == uid))
    user = user_res.scalar_one_or_none()
    if not user:
        return _empty_rewards()

    rewards = _empty_rewards()
    old_level = user.current_level or 1

    # 1 — daily activity + streak
    await _record_activity(db, uid, "task_solve")
    await _update_streak(db, uid)

    # 2 — base task XP
    base_xp = XP_TASK_AUTO_SOLVED if progress.auto_solve_used else XP_TASK_COMPLETE
    if not progress.auto_solve_used and (progress.attempt_count or 0) == 1:
        base_xp += XP_FIRST_TRY_BONUS
    if not progress.auto_solve_used and (progress.hints_used or 0) == 0:
        base_xp += XP_NO_HINTS_BONUS

    await _award_xp(db, user, base_xp, "task_complete", str(task_id))
    rewards["xp_gained"] += base_xp

    # 3 — resolve lab + course from this task
    task_res = await db.execute(select(LabTask).where(LabTask.task_id == uuid.UUID(str(task_id))))
    task_obj = task_res.scalar_one_or_none()
    lab_id = task_obj.lab_id if task_obj else None

    lab_just_completed = False
    course_just_completed = False
    course_obj = None
    lab_title = None

    if lab_id:
        lab_just_completed = await _is_lab_complete(db, uid, lab_id)
        if lab_just_completed:
            lab_res = await db.execute(select(Lab).where(Lab.lab_id == lab_id))
            lab_obj = lab_res.scalar_one_or_none()
            lab_title = lab_obj.title if lab_obj else None

            await _award_xp(db, user, XP_LAB_COMPLETE, "lab_complete", str(lab_id))
            rewards["xp_gained"] += XP_LAB_COMPLETE
            await _record_activity(db, uid, "lab_complete")

            # check course
            course_res = await db.execute(
                select(Course).join(Lab, Course.course_id == Lab.course_id)
                .where(Lab.lab_id == lab_id)
            )
            course_obj = course_res.scalar_one_or_none()
            if course_obj:
                course_just_completed = await _is_course_complete(db, uid, course_obj.course_id)
                if course_just_completed:
                    await _award_xp(db, user, XP_COURSE_COMPLETE, "course_complete",
                                    str(course_obj.course_id))
                    rewards["xp_gained"] += XP_COURSE_COMPLETE

    # 4 — level-up check
    new_level_id = await _compute_level(db, user.total_xp)
    if new_level_id > old_level:
        user.current_level = new_level_id
        lvl_res = await db.execute(select(Level).where(Level.level_id == new_level_id))
        lvl = lvl_res.scalar_one_or_none()
        rewards["level_up"] = True
        rewards["new_level"] = new_level_id
        rewards["new_level_title"] = lvl.title if lvl else None

    # 5 — badge checks
    new_badges = await _check_and_award_badges(
        db, user, uid, progress,
        lab_just_completed=lab_just_completed,
        course_just_completed=course_just_completed,
        lab_id=lab_id,
        course_obj=course_obj,
        lab_title=lab_title,
    )
    rewards["new_badges"] = [_badge_dict(b) for b in new_badges]

    await db.flush()
    return rewards


async def on_login(db: AsyncSession, user_id) -> dict:
    """Update streak + award streak XP / badges on login."""
    uid = uuid.UUID(str(user_id))

    user_res = await db.execute(select(User).where(User.user_id == uid))
    user = user_res.scalar_one_or_none()
    if not user:
        return {}

    await _record_activity(db, uid, "login")
    changed = await _update_streak(db, uid)
    new_badges = []

    if changed:
        streak_res = await db.execute(select(UserStreak).where(UserStreak.user_id == uid))
        streak = streak_res.scalar_one_or_none()
        cs = streak.current_streak if streak else 0

        if cs == 7:
            await _award_xp(db, user, XP_STREAK_7, "streak_7_bonus")
        elif cs == 30:
            await _award_xp(db, user, XP_STREAK_30, "streak_30_bonus")

        # check streak badges only
        badges_res = await db.execute(select(Badge).where(Badge.is_active == True))
        all_badges = badges_res.scalars().all()
        earned_res = await db.execute(select(UserBadge.badge_id).where(UserBadge.user_id == uid))
        earned_ids = set(earned_res.scalars().all())

        for badge in all_badges:
            if badge.badge_id in earned_ids:
                continue
            c = badge.criteria or {}
            if c.get("type") == "streak_days" and cs >= c.get("days", 0):
                db.add(UserBadge(user_id=uid, badge_id=badge.badge_id))
                earned_ids.add(badge.badge_id)
                new_badges.append(badge)
                if badge.xp_reward > 0:
                    await _award_xp(db, user, badge.xp_reward, f"badge_{badge.slug}",
                                    str(badge.badge_id))

        await _compute_and_set_level(db, user)

    await db.flush()
    return {"streak_updated": changed, "new_badges": [_badge_dict(b) for b in new_badges]}


async def get_profile(db: AsyncSession, user_id) -> dict:
    """Full gamification profile for the given user."""
    uid = uuid.UUID(str(user_id))

    user_res = await db.execute(select(User).where(User.user_id == uid))
    user = user_res.scalar_one_or_none()
    if not user:
        return {}

    streak_res = await db.execute(select(UserStreak).where(UserStreak.user_id == uid))
    streak = streak_res.scalar_one_or_none()

    badges_res = await db.execute(
        select(UserBadge).options(selectinload(UserBadge.badge))
        .where(UserBadge.user_id == uid)
        .order_by(UserBadge.awarded_at.desc())
    )
    user_badges = badges_res.scalars().all()

    total_xp = user.total_xp or 0
    level_id = user.current_level or 1
    levels_res = await db.execute(select(Level).order_by(Level.level_id))
    levels = levels_res.scalars().all()

    current_lv = next((l for l in levels if l.level_id == level_id), None)
    next_lv = next((l for l in levels if l.level_id == level_id + 1), None)

    if current_lv and next_lv:
        xp_in = total_xp - current_lv.min_xp
        xp_span = next_lv.min_xp - current_lv.min_xp
        pct = min(100, int(xp_in / xp_span * 100)) if xp_span > 0 else 100
        xp_to_next = max(0, next_lv.min_xp - total_xp)
    else:
        pct = 100
        xp_to_next = 0

    tasks_res = await db.execute(
        select(func.count(LabProgress.progress_id)).where(
            LabProgress.user_id == uid,
            LabProgress.status.in_(["completed", "auto_solved"]),
        )
    )
    tasks_completed = tasks_res.scalar() or 0
    labs_completed = await _count_completed_labs(db, uid)
    courses_completed = await _count_completed_courses(db, uid)

    return {
        "xp": {
            "total_xp": total_xp,
            "current_level": level_id,
            "level_title": current_lv.title if current_lv else "Recruit",
            "xp_to_next_level": xp_to_next,
            "progress_pct": pct,
        },
        "streak": {
            "current_streak": streak.current_streak if streak else 0,
            "longest_streak": streak.longest_streak if streak else 0,
            "last_active_date": streak.last_active_date.isoformat() if streak and streak.last_active_date else None,
            "total_active_days": streak.total_active_days if streak else 0,
        },
        "badges": [_user_badge_dict(ub) for ub in user_badges if ub.badge],
        "labs_completed": labs_completed,
        "courses_completed": courses_completed,
        "tasks_completed": tasks_completed,
    }


async def get_xp_history(db: AsyncSession, user_id, limit: int = 20) -> list:
    uid = uuid.UUID(str(user_id))
    result = await db.execute(
        select(XPLog).where(XPLog.user_id == uid)
        .order_by(XPLog.created_at.desc()).limit(limit)
    )
    return [
        {"amount": l.amount, "reason": l.reason, "created_at": l.created_at.isoformat()}
        for l in result.scalars().all()
    ]


async def get_activity_heatmap(db: AsyncSession, user_id, days: int = 90) -> list:
    uid = uuid.UUID(str(user_id))
    cutoff = date.today() - timedelta(days=days)

    result = await db.execute(
        select(ActivityLog.activity_date, func.sum(ActivityLog.count).label("total"))
        .where(ActivityLog.user_id == uid, ActivityLog.activity_date >= cutoff)
        .group_by(ActivityLog.activity_date)
        .order_by(ActivityLog.activity_date)
    )
    return [{"date": r.activity_date.isoformat(), "count": r.total} for r in result.all()]


async def get_leaderboard(db: AsyncSession, limit: int = 50, current_user_id=None) -> dict:
    result = await db.execute(
        select(User).where(User.is_active == True)
        .order_by(User.total_xp.desc())
        .limit(limit)
    )
    users = result.scalars().all()

    lvls_res = await db.execute(select(Level).order_by(Level.level_id))
    lvl_map = {l.level_id: l for l in lvls_res.scalars().all()}

    entries = []
    for i, u in enumerate(users):
        lv = lvl_map.get(u.current_level or 1)
        streak_res = await db.execute(select(UserStreak).where(UserStreak.user_id == u.user_id))
        streak = streak_res.scalar_one_or_none()
        labs = await _count_completed_labs(db, u.user_id)
        entries.append({
            "rank": i + 1,
            "user_id": str(u.user_id),
            "full_name": u.full_name,
            "total_xp": u.total_xp or 0,
            "current_level": u.current_level or 1,
            "level_title": lv.title if lv else "Recruit",
            "labs_completed": labs,
            "current_streak": streak.current_streak if streak else 0,
        })

    my_rank = None
    if current_user_id:
        cuid = str(uuid.UUID(str(current_user_id)))
        for e in entries:
            if e["user_id"] == cuid:
                my_rank = e["rank"]
                break

    return {"entries": entries, "total": len(entries), "my_rank": my_rank}


async def get_all_badges(db: AsyncSession, user_id=None) -> list:
    """Return all badges, marking which ones the user has earned."""
    badges_res = await db.execute(
        select(Badge).where(Badge.is_active == True).order_by(Badge.category, Badge.xp_reward)
    )
    all_badges = badges_res.scalars().all()

    earned_ids = set()
    earned_dates = {}
    if user_id:
        uid = uuid.UUID(str(user_id))
        ub_res = await db.execute(
            select(UserBadge).where(UserBadge.user_id == uid)
        )
        for ub in ub_res.scalars().all():
            earned_ids.add(ub.badge_id)
            earned_dates[ub.badge_id] = ub.awarded_at.isoformat()

    return [
        {
            **_badge_dict(b),
            "earned": b.badge_id in earned_ids,
            "awarded_at": earned_dates.get(b.badge_id),
        }
        for b in all_badges
    ]


async def mark_badges_seen(db: AsyncSession, user_id) -> None:
    uid = uuid.UUID(str(user_id))
    result = await db.execute(
        select(UserBadge).where(UserBadge.user_id == uid, UserBadge.seen == False)
    )
    for ub in result.scalars().all():
        ub.seen = True
    await db.flush()


# ─── Internal helpers ─────────────────────────────────────────────────────────

async def _award_xp(db, user: User, amount: int, reason: str, ref_id=None) -> int:
    if amount <= 0:
        return 0
    user.total_xp = (user.total_xp or 0) + amount
    db.add(XPLog(user_id=user.user_id, amount=amount, reason=reason, reference_id=ref_id))
    return amount


async def _update_streak(db: AsyncSession, user_id: uuid.UUID) -> bool:
    today = date.today()
    result = await db.execute(select(UserStreak).where(UserStreak.user_id == user_id))
    streak = result.scalar_one_or_none()

    if not streak:
        db.add(UserStreak(
            user_id=user_id, current_streak=1, longest_streak=1,
            last_active_date=today, total_active_days=1,
        ))
        return True

    if streak.last_active_date == today:
        return False

    yesterday = today - timedelta(days=1)
    streak.current_streak = (streak.current_streak + 1) if streak.last_active_date == yesterday else 1
    streak.longest_streak = max(streak.longest_streak, streak.current_streak)
    streak.last_active_date = today
    streak.total_active_days = (streak.total_active_days or 0) + 1
    streak.updated_at = datetime.now(timezone.utc)
    return True


async def _record_activity(db: AsyncSession, user_id: uuid.UUID, activity_type: str) -> None:
    today = date.today()
    result = await db.execute(
        select(ActivityLog).where(
            ActivityLog.user_id == user_id,
            ActivityLog.activity_date == today,
            ActivityLog.activity_type == activity_type,
        )
    )
    log = result.scalar_one_or_none()
    if log:
        log.count += 1
    else:
        db.add(ActivityLog(user_id=user_id, activity_date=today, activity_type=activity_type))


async def _compute_level(db: AsyncSession, total_xp: int) -> int:
    total_xp = total_xp or 0
    result = await db.execute(
        select(Level).where(Level.min_xp <= total_xp)
        .order_by(Level.min_xp.desc()).limit(1)
    )
    level = result.scalar_one_or_none()
    return level.level_id if level else 1


async def _compute_and_set_level(db: AsyncSession, user: User) -> None:
    new_lv = await _compute_level(db, user.total_xp or 0)
    if new_lv != (user.current_level or 1):
        user.current_level = new_lv


async def _is_lab_complete(db: AsyncSession, user_id: uuid.UUID, lab_id: uuid.UUID) -> bool:
    total_res = await db.execute(
        select(func.count(LabTask.task_id)).where(LabTask.lab_id == lab_id)
    )
    total = total_res.scalar() or 0
    if total == 0:
        return False

    done_res = await db.execute(
        select(func.count(LabProgress.progress_id)).where(
            LabProgress.user_id == user_id,
            LabProgress.lab_id == lab_id,
            LabProgress.status.in_(["completed", "auto_solved"]),
        )
    )
    done = done_res.scalar() or 0
    return done >= total


async def _is_course_complete(db: AsyncSession, user_id: uuid.UUID, course_id: uuid.UUID) -> bool:
    labs_res = await db.execute(
        select(Lab).where(Lab.course_id == course_id, Lab.is_published == True)
    )
    labs = labs_res.scalars().all()
    if not labs:
        return False

    for lab in labs:
        if not await _is_lab_complete(db, user_id, lab.lab_id):
            return False
    return True


async def _count_completed_labs(db: AsyncSession, user_id: uuid.UUID) -> int:
    labs_res = await db.execute(select(Lab).where(Lab.is_published == True))
    count = 0
    for lab in labs_res.scalars().all():
        if await _is_lab_complete(db, user_id, lab.lab_id):
            count += 1
    return count


async def _count_completed_courses(db: AsyncSession, user_id: uuid.UUID) -> int:
    courses_res = await db.execute(select(Course).where(Course.is_published == True))
    count = 0
    for course in courses_res.scalars().all():
        if await _is_course_complete(db, user_id, course.course_id):
            count += 1
    return count


async def _check_and_award_badges(
    db: AsyncSession,
    user: User,
    user_id: uuid.UUID,
    progress: LabProgress,
    lab_just_completed: bool,
    course_just_completed: bool,
    lab_id=None,
    course_obj=None,
    lab_title=None,
) -> list:
    badges_res = await db.execute(select(Badge).where(Badge.is_active == True))
    all_badges = badges_res.scalars().all()

    earned_res = await db.execute(select(UserBadge.badge_id).where(UserBadge.user_id == user_id))
    earned_ids = set(earned_res.scalars().all())

    # Gather counts
    tasks_res = await db.execute(
        select(func.count(LabProgress.progress_id)).where(
            LabProgress.user_id == user_id,
            LabProgress.status.in_(["completed", "auto_solved"]),
        )
    )
    task_count = tasks_res.scalar() or 0

    lab_count = await _count_completed_labs(db, user_id)
    course_count = await _count_completed_courses(db, user_id)

    streak_res = await db.execute(select(UserStreak).where(UserStreak.user_id == user_id))
    streak = streak_res.scalar_one_or_none()
    current_streak = streak.current_streak if streak else 0

    total_xp = user.total_xp or 0

    first_try_res = await db.execute(
        select(func.count(LabProgress.progress_id)).where(
            LabProgress.user_id == user_id,
            LabProgress.attempt_count == 1,
            LabProgress.is_correct == True,
            LabProgress.auto_solve_used == False,
        )
    )
    first_try_count = first_try_res.scalar() or 0

    task_no_hints = (
        not progress.auto_solve_used
        and (progress.hints_used or 0) == 0
        and progress.is_correct
    )

    lab_no_hints = False
    if lab_just_completed and lab_id:
        hints_res = await db.execute(
            select(func.count(LabProgress.progress_id)).where(
                LabProgress.user_id == user_id,
                LabProgress.lab_id == lab_id,
                LabProgress.hints_used > 0,
            )
        )
        lab_no_hints = (hints_res.scalar() or 0) == 0

    course_no_hints = False
    course_title = course_obj.title if course_obj else None
    if course_just_completed and course_obj:
        hints_in_course_res = await db.execute(
            select(func.count(LabProgress.progress_id))
            .join(Lab, LabProgress.lab_id == Lab.lab_id)
            .where(
                LabProgress.user_id == user_id,
                Lab.course_id == course_obj.course_id,
                LabProgress.hints_used > 0,
            )
        )
        course_no_hints = (hints_in_course_res.scalar() or 0) == 0

    new_badges = []
    for badge in all_badges:
        if badge.badge_id in earned_ids:
            continue
        c = badge.criteria or {}
        btype = c.get("type", "")
        earned = False

        if btype == "task_count":
            earned = task_count >= c.get("threshold", 1)
        elif btype == "lab_count":
            earned = lab_count >= c.get("threshold", 1)
        elif btype == "course_count":
            earned = course_count >= c.get("threshold", 1)
        elif btype == "xp_total":
            earned = total_xp >= c.get("amount", 0)
        elif btype == "streak_days":
            earned = current_streak >= c.get("days", 0)
        elif btype == "no_hints_task":
            earned = task_no_hints
        elif btype == "no_hints_lab":
            earned = lab_no_hints
        elif btype == "no_hints_course":
            earned = course_no_hints
        elif btype == "first_try_count":
            earned = first_try_count >= c.get("threshold", 1)
        elif btype == "course_complete":
            req = c.get("course_title", "")
            earned = course_just_completed and course_title and req.lower() in course_title.lower()
        elif btype == "lab_complete":
            req = c.get("lab_title", "")
            earned = lab_just_completed and lab_title and req.lower() in lab_title.lower()

        if earned:
            db.add(UserBadge(user_id=user_id, badge_id=badge.badge_id))
            earned_ids.add(badge.badge_id)
            new_badges.append(badge)
            if badge.xp_reward > 0:
                await _award_xp(db, user, badge.xp_reward, f"badge_{badge.slug}", str(badge.badge_id))

    return new_badges


# ─── Serialisation helpers ────────────────────────────────────────────────────

def _badge_dict(b: Badge) -> dict:
    return {
        "badge_id": str(b.badge_id),
        "slug": b.slug,
        "name": b.name,
        "description": b.description,
        "icon": b.icon,
        "rarity": b.rarity,
        "category": b.category,
        "xp_reward": b.xp_reward,
    }


def _user_badge_dict(ub: UserBadge) -> dict:
    return {
        **_badge_dict(ub.badge),
        "awarded_at": ub.awarded_at.isoformat(),
        "seen": ub.seen,
    }


def _empty_rewards() -> dict:
    return {
        "xp_gained": 0,
        "level_up": False,
        "new_level": None,
        "new_level_title": None,
        "new_badges": [],
    }
