import asyncio
import subprocess
from functools import partial
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError

from app.core.config import settings
from app.core.database import get_db, async_session
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.models.lab import Lab, LabTask, Hint
from app.models.lab_instance import LabInstance, LabProgress, LabHintCooldown
from app.schemas.lab import (
    LabCreate,
    LabResponse,
    LabDetailResponse,
    TaskCreate,
    TaskResponse,
    HintCreate,
    HintResponse,
    HintAvailability,
    RevealedHintsResponse,
    GlobalCooldownResponse,
    LabInstanceResponse,
    LabProgressResponse,
    TaskProgressResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)

# ── Global hint cooldown: one shared 30-second window per user per lab ─────────
HINT_COOLDOWN_SECONDS = 30
from app.services.lab_runtime_service import (
    start_ssh_lab, stop_ssh_lab, reset_ssh_lab, autosolve_ssh_lab,
    check_ssh_lab, get_guacamole_terminal_url, get_guacamole_defender_url,
    start_df_kali_lab, stop_df_kali_lab, reset_df_kali_lab,
    autosolve_df_kali_lab, check_df_kali_lab, get_df_kali_terminal_url,
    DF_KALI_SCENARIO_DIR, TERMINAL_SCENARIO_DIR,
)
from app.services import guac_autosolve
from app.services.lab_runtime_service_metasploit import (
    start_meta_lab, stop_meta_lab, reset_meta_lab,
    autosolve_meta_lab, check_meta_lab, get_meta_terminal_url,
    get_meta_machines_info,
)
from app.schemas.auth import MessageResponse
from app.services import gamification_service as _gs

router = APIRouter(prefix="/api/labs", tags=["Labs"])


async def _try_award_certificate(db: AsyncSession, user_id, task_id) -> None:
    """Auto-generate a certificate if the user has now completed the full course."""
    import uuid as _uuid
    from app.models.course import Course
    from app.models.user import User as _User
    from app.services import certificate_service as _cert

    uid = _uuid.UUID(str(user_id))

    # Resolve course from this task
    result = await db.execute(
        select(Course)
        .join(Lab, Course.course_id == Lab.course_id)
        .join(LabTask, Lab.lab_id == LabTask.lab_id)
        .where(LabTask.task_id == _uuid.UUID(str(task_id)))
    )
    course = result.scalar_one_or_none()
    if not course:
        return

    # Skip if certificate already exists
    if await _cert.get_existing_cert(db, uid, course.course_id):
        return

    # Check completion
    is_complete, total, _ = await _cert.check_course_completion(db, uid, course.course_id)
    if not is_complete or total == 0:
        return

    # Look up the user's name
    user_res = await db.execute(select(_User).where(_User.user_id == uid))
    user = user_res.scalar_one_or_none()
    if not user:
        return

    await _cert.generate_certificate(
        db=db,
        user_id=uid,
        course_id=course.course_id,
        student_name=user.full_name,
        course_name=course.title,
    )


# ── Lab CRUD ──────────────────────────────────────────────────────────────────

@router.put("/{lab_id}", response_model=LabResponse)
async def update_lab(
    lab_id: UUID,
    req: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "system_admin")),
):
    result = await db.execute(select(Lab).where(Lab.lab_id == lab_id))
    lab = result.scalar_one_or_none()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")

    allowed = {"title", "description", "difficulty", "has_auto_solve",
               "max_duration_minutes", "sort_order", "is_published"}
    for field, value in req.items():
        if field in allowed:
            setattr(lab, field, value)

    await db.flush()
    await db.refresh(lab)
    return lab


@router.get("/{lab_id}", response_model=LabDetailResponse)
async def get_lab(
    lab_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Lab)
        .options(selectinload(Lab.tasks).selectinload(LabTask.hints))
        .where(Lab.lab_id == lab_id, Lab.is_published == True)
    )
    lab = result.scalar_one_or_none()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")

    tasks = [
        TaskResponse(
            task_id=t.task_id,
            lab_id=t.lab_id,
            title=t.title,
            instructions=t.instructions,
            sort_order=t.sort_order,
            hint_count=len(t.hints),
            has_autosolve=bool(t.autosolve_commands),
        )
        for t in lab.tasks
    ]

    cfg = lab.docker_compose_config if isinstance(lab.docker_compose_config, dict) else {}
    runtime_slug = cfg.get("runtime_slug")
    runtime_terminal = cfg.get("terminal_type")
    runtime = None
    if runtime_slug or runtime_terminal:
        runtime = {
            "slug": runtime_slug,
            "terminal_type": runtime_terminal or (
                "df-kali" if runtime_slug == "df-kali"
                else "dual" if runtime_slug == "ssh-bruteforce"
                else "single"
            ),
        }

    return LabDetailResponse(
        lab_id=lab.lab_id,
        course_id=lab.course_id,
        title=lab.title,
        description=lab.description,
        difficulty=lab.difficulty,
        has_auto_solve=lab.has_auto_solve,
        max_duration_minutes=lab.max_duration_minutes,
        sort_order=lab.sort_order,
        is_published=lab.is_published,
        docker_compose_config=lab.docker_compose_config,
        runtime=runtime,
        terminal_type=runtime_terminal,
        created_at=lab.created_at,
        tasks=tasks,
    )


# ── Lab instance lifecycle ─────────────────────────────────────────────────────

@router.post("/{lab_id}/start", response_model=LabInstanceResponse, status_code=status.HTTP_201_CREATED)
async def start_lab(
    lab_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Lab).where(Lab.lab_id == lab_id, Lab.is_published == True))
    lab = result.scalar_one_or_none()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")

    active = await db.execute(
        select(LabInstance).where(
            LabInstance.user_id == current_user.user_id,
            LabInstance.lab_id == lab_id,
            LabInstance.status.in_(["starting", "running", "paused"]),
        )
    )
    if active.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="You already have an active instance for this lab")

    instance = LabInstance(
        user_id=current_user.user_id,
        lab_id=lab_id,
        status="running",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=lab.max_duration_minutes),
    )
    db.add(instance)
    await db.flush()
    await db.refresh(instance)
    return instance


@router.post("/{lab_id}/stop", response_model=MessageResponse)
async def stop_lab(
    lab_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(LabInstance).where(
            LabInstance.user_id == current_user.user_id,
            LabInstance.lab_id == lab_id,
            LabInstance.status.in_(["starting", "running", "paused"]),
        )
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="No active lab instance found")

    instance.status = "terminated"
    instance.terminated_at = datetime.now(timezone.utc)
    return MessageResponse(message="Lab instance terminated")


@router.get("/{lab_id}/status", response_model=LabInstanceResponse)
async def lab_status(
    lab_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(LabInstance).where(
            LabInstance.user_id == current_user.user_id,
            LabInstance.lab_id == lab_id,
            LabInstance.status.in_(["starting", "running", "paused"]),
        )
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="No active lab instance found")
    return instance


# ── Lab progress ───────────────────────────────────────────────────────────────

@router.get("/{lab_id}/my-progress", response_model=LabProgressResponse)
async def get_lab_progress(
    lab_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return per-task progress for the current user in a lab."""
    # Verify lab exists
    lab_result = await db.execute(
        select(Lab).options(selectinload(Lab.tasks))
        .where(Lab.lab_id == lab_id, Lab.is_published == True)
    )
    lab = lab_result.scalar_one_or_none()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")

    total_count = len(lab.tasks)
    task_ids = [t.task_id for t in lab.tasks]

    if not task_ids:
        return LabProgressResponse(
            lab_id=lab_id, tasks=[], completed_count=0, total_count=0, percent=0
        )

    progress_result = await db.execute(
        select(LabProgress).where(
            LabProgress.user_id == current_user.user_id,
            LabProgress.lab_id == lab_id,
        )
    )
    progress_rows = progress_result.scalars().all()
    progress_by_task = {p.task_id: p for p in progress_rows}

    tasks_out = []
    completed_count = 0
    for t in lab.tasks:
        p = progress_by_task.get(t.task_id)
        if p:
            tasks_out.append(TaskProgressResponse(
                task_id=t.task_id,
                status=p.status,
                submitted_answer=p.submitted_answer,
                is_correct=p.is_correct,
                hints_used=p.hints_used,
                auto_solve_used=p.auto_solve_used,
            ))
            if p.status in ("completed", "auto_solved"):
                completed_count += 1
        else:
            tasks_out.append(TaskProgressResponse(
                task_id=t.task_id,
                status="not_started",
                hints_used=0,
            ))

    percent = round(completed_count / total_count * 100) if total_count else 0
    return LabProgressResponse(
        lab_id=lab_id,
        tasks=tasks_out,
        completed_count=completed_count,
        total_count=total_count,
        percent=percent,
    )


# ── Answer submission & hints ─────────────────────────────────────────────────

@router.post("/tasks/{task_id}/submit", response_model=SubmitAnswerResponse)
async def submit_answer(
    task_id: UUID,
    req: SubmitAnswerRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(LabTask).where(LabTask.task_id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    is_correct = False
    if task.expected_answer:
        is_correct = req.answer.strip().lower() == task.expected_answer.strip().lower()

    progress_result = await db.execute(
        select(LabProgress).where(
            LabProgress.user_id == current_user.user_id,
            LabProgress.task_id == task_id,
        )
    )
    progress = progress_result.scalar_one_or_none()
    now = datetime.now(timezone.utc)

    if not progress:
        progress = LabProgress(
            user_id=current_user.user_id,
            lab_id=task.lab_id,
            task_id=task_id,
            status="in_progress",
            attempt_count=1,
            submitted_answer=req.answer.strip(),
            is_correct=is_correct,
            started_at=now,
        )
        db.add(progress)
    else:
        progress.attempt_count = (progress.attempt_count or 0) + 1
        progress.submitted_answer = req.answer.strip()
        progress.is_correct = is_correct

    if is_correct and progress.status not in ("completed", "auto_solved"):
        progress.status = "completed"
        progress.completed_at = now

    await db.flush()

    rewards = {}
    if is_correct:
        try:
            await _try_award_certificate(db, current_user.user_id, task_id)
        except Exception:
            pass  # non-fatal
        try:
            rewards = await _gs.on_task_complete(db, current_user.user_id, task_id, progress)
        except Exception:
            pass  # non-fatal — gamification must never block submission

    return SubmitAnswerResponse(
        is_correct=is_correct,
        status=progress.status,
        message="Correct answer!" if is_correct else "Incorrect. Try again.",
        xp_gained=rewards.get("xp_gained", 0),
        level_up=rewards.get("level_up", False),
        new_level=rewards.get("new_level"),
        new_level_title=rewards.get("new_level_title"),
        new_badges=rewards.get("new_badges", []),
    )


def _cooldown_ends_at_iso(last_hint_at: datetime) -> str:
    return (last_hint_at + timedelta(seconds=HINT_COOLDOWN_SECONDS)).isoformat()


async def _get_lab_cooldown(db: AsyncSession, user_id, lab_id) -> tuple[int, str | None]:
    """Return (seconds_remaining, global_cooldown_ends_at_iso) for the given user+lab."""
    row = await db.execute(
        select(LabHintCooldown).where(
            LabHintCooldown.user_id == user_id,
            LabHintCooldown.lab_id == lab_id,
        )
    )
    cooldown = row.scalar_one_or_none()
    if not cooldown:
        return 0, None
    now = datetime.now(timezone.utc)
    elapsed = (now - cooldown.last_hint_at).total_seconds()
    remaining = max(0, int(HINT_COOLDOWN_SECONDS - elapsed))
    if remaining == 0:
        return 0, None
    return remaining, _cooldown_ends_at_iso(cooldown.last_hint_at)


async def _touch_lab_cooldown(db: AsyncSession, user_id, lab_id, now: datetime) -> None:
    """Upsert the global cooldown timestamp for this user+lab."""
    row = await db.execute(
        select(LabHintCooldown).where(
            LabHintCooldown.user_id == user_id,
            LabHintCooldown.lab_id == lab_id,
        )
    )
    cooldown = row.scalar_one_or_none()
    if cooldown:
        cooldown.last_hint_at = now
    else:
        db.add(LabHintCooldown(user_id=user_id, lab_id=lab_id, last_hint_at=now))
    await db.flush()


@router.get("/{lab_id}/hint-cooldown", response_model=GlobalCooldownResponse)
async def get_lab_hint_cooldown(
    lab_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the current global hint cooldown state for this user in this lab.
    Called on page load to restore the shared timer across all tasks."""
    seconds_remaining, cooldown_ends_at = await _get_lab_cooldown(
        db, current_user.user_id, lab_id
    )
    return GlobalCooldownResponse(
        seconds_remaining=seconds_remaining,
        global_cooldown_ends_at=cooldown_ends_at,
    )


@router.get("/tasks/{task_id}/hint", response_model=HintAvailability)
async def request_hint(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Unlock the next hint for a task.
    Enforces a GLOBAL 30-second cooldown shared across ALL tasks in the same lab."""
    total_result = await db.execute(
        select(func.count(Hint.hint_id)).where(Hint.task_id == task_id)
    )
    total_hints = total_result.scalar()
    if total_hints == 0:
        raise HTTPException(status_code=404, detail="No hints available")

    task_result = await db.execute(select(LabTask).where(LabTask.task_id == task_id))
    task = task_result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    now = datetime.now(timezone.utc)

    # ── Check global lab-level cooldown (blocks ALL tasks) ────────────────────
    secs_remaining, cooldown_ends_at = await _get_lab_cooldown(
        db, current_user.user_id, task.lab_id
    )
    if secs_remaining > 0:
        progress_result = await db.execute(
            select(LabProgress).where(
                LabProgress.user_id == current_user.user_id,
                LabProgress.task_id == task_id,
            )
        )
        progress = progress_result.scalar_one_or_none()
        hints_used = progress.hints_used if progress else 0
        return HintAvailability(
            is_available=False,
            total_hints=total_hints,
            hints_used=hints_used,
            seconds_remaining=secs_remaining,
            global_cooldown_ends_at=cooldown_ends_at,
        )

    # ── Load / create per-task progress ──────────────────────────────────────
    progress_result = await db.execute(
        select(LabProgress).where(
            LabProgress.user_id == current_user.user_id,
            LabProgress.task_id == task_id,
        )
    )
    progress = progress_result.scalar_one_or_none()
    if not progress:
        progress = LabProgress(
            user_id=current_user.user_id,
            lab_id=task.lab_id,
            task_id=task_id,
            status="in_progress",
            started_at=now,
        )
        db.add(progress)
        await db.flush()

    hints_used = progress.hints_used
    if hints_used >= total_hints:
        return HintAvailability(
            is_available=False, total_hints=total_hints,
            hints_used=hints_used, seconds_remaining=0,
        )

    next_hint_result = await db.execute(
        select(Hint).where(Hint.task_id == task_id, Hint.hint_order == hints_used + 1)
    )
    next_hint = next_hint_result.scalar_one_or_none()
    if not next_hint:
        raise HTTPException(status_code=404, detail="Next hint not found")

    # ── Reveal the hint ───────────────────────────────────────────────────────
    progress.hints_used += 1
    progress.last_hint_at = now
    await db.flush()

    # Update global lab-level cooldown (blocks every other task's hint for 30s)
    await _touch_lab_cooldown(db, current_user.user_id, task.lab_id, now)

    global_ends_at = _cooldown_ends_at_iso(now)

    return HintAvailability(
        is_available=True,
        hint=HintResponse(
            hint_id=next_hint.hint_id,
            hint_order=next_hint.hint_order,
            hint_text=next_hint.hint_text,
            delay_minutes=next_hint.delay_minutes,
        ),
        total_hints=total_hints,
        hints_used=progress.hints_used,
        seconds_remaining=HINT_COOLDOWN_SECONDS,
        global_cooldown_ends_at=global_ends_at,
    )


@router.get("/tasks/{task_id}/hints", response_model=RevealedHintsResponse)
async def get_revealed_hints(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all hints this user has already unlocked for a task.
    Cooldown state is fetched separately via GET /labs/{lab_id}/hint-cooldown."""
    total_result = await db.execute(
        select(func.count(Hint.hint_id)).where(Hint.task_id == task_id)
    )
    total_hints = total_result.scalar() or 0

    progress_result = await db.execute(
        select(LabProgress).where(
            LabProgress.user_id == current_user.user_id,
            LabProgress.task_id == task_id,
        )
    )
    progress = progress_result.scalar_one_or_none()
    hints_used = progress.hints_used if progress else 0

    revealed: list[HintResponse] = []
    if hints_used > 0:
        hints_result = await db.execute(
            select(Hint)
            .where(Hint.task_id == task_id, Hint.hint_order <= hints_used)
            .order_by(Hint.hint_order)
        )
        revealed = [
            HintResponse(
                hint_id=h.hint_id,
                hint_order=h.hint_order,
                hint_text=h.hint_text,
                delay_minutes=h.delay_minutes,
            )
            for h in hints_result.scalars().all()
        ]

    return RevealedHintsResponse(
        hints=revealed,
        hints_used=hints_used,
        total_hints=total_hints,
    )


@router.post("/tasks/{task_id}/auto-solve", response_model=MessageResponse)
async def auto_solve_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark task as auto-solved (called after WS autosolve completes)."""
    task_result = await db.execute(
        select(LabTask).options(selectinload(LabTask.hints)).where(LabTask.task_id == task_id)
    )
    task = task_result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    lab_result = await db.execute(select(Lab).where(Lab.lab_id == task.lab_id))
    lab = lab_result.scalar_one_or_none()
    if not lab or not lab.has_auto_solve:
        raise HTTPException(status_code=403, detail="Auto-solve not available for this lab")

    progress_result = await db.execute(
        select(LabProgress).where(
            LabProgress.user_id == current_user.user_id,
            LabProgress.task_id == task_id,
        )
    )
    progress = progress_result.scalar_one_or_none()
    now = datetime.now(timezone.utc)

    if not progress:
        progress = LabProgress(
            user_id=current_user.user_id,
            lab_id=task.lab_id,
            task_id=task_id,
            status="auto_solved",
            auto_solve_used=True,
            is_correct=True,
            submitted_answer=task.expected_answer,
            started_at=now,
            completed_at=now,
        )
        db.add(progress)
    else:
        progress.status = "auto_solved"
        progress.auto_solve_used = True
        progress.is_correct = True
        if task.expected_answer:
            progress.submitted_answer = task.expected_answer
        progress.completed_at = now

    await db.flush()
    return MessageResponse(message="Auto-solve recorded")


# ── Lab and task admin CRUD ───────────────────────────────────────────────────

@router.post("", response_model=LabResponse, status_code=status.HTTP_201_CREATED)
async def create_lab(
    req: LabCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "system_admin")),
):
    lab = Lab(**req.model_dump())
    db.add(lab)
    await db.flush()
    await db.refresh(lab)
    return lab


@router.post("/{lab_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    lab_id: UUID,
    req: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "system_admin")),
):
    result = await db.execute(select(Lab).where(Lab.lab_id == lab_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Lab not found")

    task = LabTask(lab_id=lab_id, **req.model_dump())
    db.add(task)
    await db.flush()
    await db.refresh(task)

    return TaskResponse(
        task_id=task.task_id,
        lab_id=task.lab_id,
        title=task.title,
        instructions=task.instructions,
        sort_order=task.sort_order,
        hint_count=0,
        has_autosolve=bool(task.autosolve_commands),
    )


@router.post("/{lab_id}/tasks/{task_id}/hints", response_model=HintResponse,
             status_code=status.HTTP_201_CREATED)
async def create_hint(
    lab_id: UUID,
    task_id: UUID,
    req: HintCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "system_admin")),
):
    result = await db.execute(
        select(LabTask).where(LabTask.task_id == task_id, LabTask.lab_id == lab_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found in this lab")

    hint = Hint(task_id=task_id, **req.model_dump())
    db.add(hint)
    await db.flush()
    await db.refresh(hint)
    return hint


# ── Autosolve WebSocket ───────────────────────────────────────────────────────

@router.websocket("/ws/autosolve/{task_id}")
async def ws_autosolve(
    websocket: WebSocket,
    task_id: UUID,
    token: str = Query(None),
):
    """
    Stream autosolve command execution for a task.
    Authenticates via ?token= query param (JWT access token).
    Runs autosolve_commands in the df-kali container and streams output.
    Sends {"type":"answer","data":"..."} at the end so the frontend can fill the field.
    """
    await websocket.accept()

    # ── Authenticate via query-param token ────────────────────────────────────
    user_id = None
    try:
        if not token:
            raise ValueError("No token")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            raise ValueError("Not an access token")
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Missing sub")
    except (JWTError, ValueError) as exc:
        await websocket.send_json({"type": "error", "data": f"Unauthorized: {exc}"})
        await websocket.close(code=4001)
        return

    # ── Fetch task + lab ──────────────────────────────────────────────────────
    async with async_session() as db:
        task_result = await db.execute(
            select(LabTask).options(selectinload(LabTask.hints))
            .where(LabTask.task_id == task_id)
        )
        task = task_result.scalar_one_or_none()
        if not task:
            await websocket.send_json({"type": "error", "data": "Task not found"})
            await websocket.close()
            return

        lab_result = await db.execute(select(Lab).where(Lab.lab_id == task.lab_id))
        lab = lab_result.scalar_one_or_none()
        if not lab or not lab.has_auto_solve:
            await websocket.send_json({"type": "error", "data": "Auto-solve not available"})
            await websocket.close()
            return

        # Require all hints to be revealed first
        total_hints = len(task.hints)
        if total_hints > 0:
            progress_result = await db.execute(
                select(LabProgress).where(
                    LabProgress.user_id == user_id,
                    LabProgress.task_id == task_id,
                )
            )
            progress = progress_result.scalar_one_or_none()
            hints_used = progress.hints_used if progress else 0
            if hints_used < total_hints:
                await websocket.send_json({
                    "type": "error",
                    "data": f"Reveal all {total_hints} hints before running auto-solve",
                })
                await websocket.close()
                return

        commands = task.autosolve_commands or []
        expected_answer = task.expected_answer or ""
        cfg = lab.docker_compose_config if isinstance(lab.docker_compose_config, dict) else {}
        runtime_slug = cfg.get("runtime_slug", "df-kali")

    # Determine container name from runtime slug
    container_map = {
        "df-kali": "cyber_df_kali",
        "ssh-bruteforce": "cyber_attacker_kali",
        "metasploit": "cyber_kali_msf",
    }
    container = container_map.get(runtime_slug, "cyber_df_kali")

    if not commands:
        await websocket.send_json({
            "type": "info",
            "data": "No autosolve commands for this task (theory task).",
        })
        await websocket.send_json({"type": "answer", "data": expected_answer})
        await websocket.send_json({"type": "done"})
        await websocket.close()
        return

    # ── Stream each command ────────────────────────────────────────────────────
    try:
        for cmd in commands:
            await websocket.send_json({"type": "cmd", "data": f"$ {cmd}"})
            try:
                proc = await asyncio.create_subprocess_exec(
                    "docker", "exec", container, "bash", "-lc", cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                )
                try:
                    async for raw_line in proc.stdout:
                        line = raw_line.decode(errors="replace").rstrip()
                        await websocket.send_json({"type": "line", "data": line})
                    await proc.wait()
                except Exception:
                    pass
            except Exception as e:
                await websocket.send_json({"type": "line", "data": f"[exec error] {e}"})

        # Mark task as auto_solved in DB
        async with async_session() as db:
            progress_result = await db.execute(
                select(LabProgress).where(
                    LabProgress.user_id == user_id,
                    LabProgress.task_id == task_id,
                )
            )
            progress = progress_result.scalar_one_or_none()
            now = datetime.now(timezone.utc)
            if not progress:
                progress = LabProgress(
                    user_id=user_id,
                    lab_id=task.lab_id,
                    task_id=task_id,
                    status="auto_solved",
                    auto_solve_used=True,
                    is_correct=True,
                    submitted_answer=expected_answer,
                    started_at=now,
                    completed_at=now,
                )
                db.add(progress)
            else:
                progress.status = "auto_solved"
                progress.auto_solve_used = True
                progress.is_correct = True
                if expected_answer:
                    progress.submitted_answer = expected_answer
                progress.completed_at = now
            await db.commit()

        await websocket.send_json({"type": "answer", "data": expected_answer})
        await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "data": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


# ── Lab-level autosolve WebSocket ────────────────────────────────────────────

@router.websocket("/ws/autosolve-lab/{lab_id}")
async def ws_autosolve_lab(
    websocket: WebSocket,
    lab_id: UUID,
    token: str = Query(None),
):
    """
    AutoSolve — real VM execution via Guacamole/tmux.

    For each task that has autosolve_commands:
      1. Commands are injected into the active tmux session inside the Kali
         container, so they appear visibly in the Guacamole terminal.
      2. Commands are also executed via docker exec for clean stdout capture.
      3. Output lines stream to the frontend in real-time.
      4. Answer is extracted from real output when it matches expected_answer,
         otherwise falls back to the DB value.

    Conceptual tasks (no autosolve_commands) receive the DB expected_answer
    directly without any VM interaction.

    Protocol (server → client):
      {"type": "status",     "message": "..."}
      {"type": "start",      "total_tasks": N}
      {"type": "task_start", "task_id", "task_title", "task_index", "total"}
      {"type": "output",     "task_id", "data": "line"}
      {"type": "task_done",  "task_id", "answer": "..."}
      {"type": "done"}
      {"type": "error",      "data": "..."}
    """
    await websocket.accept()

    # ── Auth ──────────────────────────────────────────────────────────────────
    user_id = None
    try:
        if not token:
            raise ValueError("No token")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            raise ValueError("Not an access token")
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Missing sub")
    except (JWTError, ValueError) as exc:
        await websocket.send_json({"type": "error", "data": f"Unauthorized: {exc}"})
        await websocket.close(code=4001)
        return

    try:
        # ── Load lab + tasks ──────────────────────────────────────────────────
        async with async_session() as db:
            lab_result = await db.execute(
                select(Lab)
                .options(selectinload(Lab.tasks).selectinload(LabTask.hints))
                .where(Lab.lab_id == lab_id, Lab.is_published == True)
            )
            lab = lab_result.scalar_one_or_none()
            if not lab or not lab.has_auto_solve:
                await websocket.send_json({
                    "type": "error",
                    "data": "Auto-solve not available for this lab",
                })
                await websocket.close()
                return
            tasks = sorted(lab.tasks, key=lambda t: t.sort_order)

        # ── Determine Kali container from lab runtime ─────────────────────────
        cfg = lab.docker_compose_config or {}
        if not isinstance(cfg, dict):
            cfg = {}
        runtime_slug = cfg.get("runtime_slug", "df-kali")
        container = guac_autosolve.CONTAINER_MAP.get(runtime_slug, "cyber_df_kali")

        # ── Container liveness check (only when commands exist) ───────────────
        has_command_tasks = any(t.autosolve_commands for t in tasks)
        if has_command_tasks:
            loop = asyncio.get_event_loop()
            running = await loop.run_in_executor(
                None, guac_autosolve.container_is_running, container
            )
            if not running:
                await websocket.send_json({
                    "type": "error",
                    "data": (
                        f"Kali VM ({container}) is not running. "
                        "Please click 'Launch Forensics Kali', wait for it to load, "
                        "then try Auto-Solve again."
                    ),
                })
                await websocket.close()
                return

            # Create tmux session if the student hasn't opened Guacamole yet
            await websocket.send_json({
                "type":    "status",
                "message": "Connecting to Kali VM…",
            })
            await loop.run_in_executor(
                None, guac_autosolve.ensure_tmux_session, container
            )

        await websocket.send_json({"type": "start", "total_tasks": len(tasks)})

        # ── Execute every task ────────────────────────────────────────────────
        for i, task in enumerate(tasks):
            tid      = str(task.task_id)
            commands = task.autosolve_commands or []
            expected = task.expected_answer or ""

            await websocket.send_json({
                "type":       "task_start",
                "task_id":    tid,
                "task_title": task.title,
                "task_index": i,
                "total":      len(tasks),
            })

            if commands:
                # Real VM execution: tmux inject (visible) + docker exec (output)
                real_out = await guac_autosolve.run_task_commands(
                    container, commands, tid, websocket
                )
                answer = guac_autosolve.extract_answer(real_out, expected)
            else:
                # Conceptual task — answer from DB only
                answer = expected

            # Persist result + run gamification (XP, badges)
            rewards: dict = {}
            async with async_session() as db:
                progress = await _upsert_auto_solved(db, user_id, task, answer)
                try:
                    rewards = await _gs.on_task_complete(db, user_id, task.task_id, progress)
                except Exception:
                    pass
                await db.commit()

            await websocket.send_json({
                "type":       "task_done",
                "task_id":    tid,
                "answer":     answer,
                "new_badges": rewards.get("new_badges", []),
                "xp_gained":  rewards.get("xp_gained", 0),
                "level_up":   rewards.get("level_up", False),
                "new_level":  rewards.get("new_level"),
            })

            await asyncio.sleep(0.2)

        await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "data": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


async def _upsert_auto_solved(db, user_id: str, task, expected_answer: str) -> LabProgress:
    """Insert or update a LabProgress row as auto_solved. Returns the progress object."""
    progress_result = await db.execute(
        select(LabProgress).where(
            LabProgress.user_id == user_id,
            LabProgress.task_id == task.task_id,
        )
    )
    progress = progress_result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if not progress:
        progress = LabProgress(
            user_id=user_id,
            lab_id=task.lab_id,
            task_id=task.task_id,
            status="auto_solved",
            auto_solve_used=True,
            is_correct=True,
            submitted_answer=expected_answer,
            started_at=now,
            completed_at=now,
        )
        db.add(progress)
    else:
        progress.status = "auto_solved"
        progress.auto_solve_used = True
        progress.is_correct = True
        if expected_answer:
            progress.submitted_answer = expected_answer
        progress.completed_at = now
    await db.flush()
    return progress

    try:
        await _try_award_certificate(db, user_id, task.task_id)
    except Exception:
        pass  # non-fatal

    try:
        await _gs.on_task_complete(db, user_id, task.task_id, progress)
    except Exception:
        pass  # non-fatal


# ── Runtime endpoints ─────────────────────────────────────────────────────────

@router.post("/runtime/ssh-bruteforce/start")
@router.post("/runtime/single/start")
@router.post("/runtime/dual/start")
async def runtime_start_ssh_lab():
    return start_ssh_lab()

@router.post("/runtime/ssh-bruteforce/stop")
@router.post("/runtime/single/stop")
@router.post("/runtime/dual/stop")
async def runtime_stop_ssh_lab():
    return stop_ssh_lab()

@router.post("/runtime/ssh-bruteforce/reset")
@router.post("/runtime/single/reset")
@router.post("/runtime/dual/reset")
async def runtime_reset_ssh_lab():
    return reset_ssh_lab()

@router.post("/runtime/ssh-bruteforce/autosolve")
@router.post("/runtime/single/autosolve")
@router.post("/runtime/dual/autosolve")
async def runtime_autosolve_ssh_lab():
    return autosolve_ssh_lab()

@router.get("/runtime/ssh-bruteforce/check")
@router.get("/runtime/single/check")
@router.get("/runtime/dual/check")
async def runtime_check_ssh_lab():
    return check_ssh_lab()

@router.get("/runtime/ssh-bruteforce/terminal-url")
@router.get("/runtime/single/terminal-url")
@router.get("/runtime/dual/terminal-url")
async def runtime_terminal_url():
    return get_guacamole_terminal_url()

@router.get("/runtime/ssh-bruteforce/defender-url")
@router.get("/runtime/dual/defender-url")
async def runtime_defender_url():
    return get_guacamole_defender_url()

@router.post("/runtime/metasploit/start")
async def runtime_start_meta_lab():
    return start_meta_lab()

@router.post("/runtime/metasploit/stop")
async def runtime_stop_meta_lab():
    return stop_meta_lab()

@router.post("/runtime/metasploit/reset")
async def runtime_reset_meta_lab():
    return reset_meta_lab()

@router.post("/runtime/metasploit/autosolve")
async def runtime_autosolve_meta_lab():
    return autosolve_meta_lab()

@router.get("/runtime/metasploit/check")
async def runtime_check_meta_lab():
    return check_meta_lab()

@router.get("/runtime/metasploit/terminal-url")
async def runtime_meta_terminal_url():
    return get_meta_terminal_url()

@router.get("/runtime/metasploit/machines")
async def runtime_meta_machines():
    return get_meta_machines_info()

@router.post("/runtime/df-kali/start")
async def runtime_start_df_kali():
    return start_df_kali_lab()

@router.post("/runtime/df-kali/stop")
async def runtime_stop_df_kali():
    return stop_df_kali_lab()

@router.post("/runtime/df-kali/reset")
async def runtime_reset_df_kali():
    return reset_df_kali_lab()

@router.post("/runtime/df-kali/autosolve")
async def runtime_autosolve_df_kali():
    return autosolve_df_kali_lab()

@router.get("/runtime/df-kali/check")
async def runtime_check_df_kali():
    return check_df_kali_lab()

@router.get("/runtime/df-kali/terminal-url")
async def runtime_df_kali_terminal_url():
    return get_df_kali_terminal_url()

@router.post("/runtime/df-kali/scroll")
async def runtime_scroll_df_kali(direction: str = "up"):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, guac_autosolve.scroll_terminal, "cyber_df_kali", direction)
    return {"success": True}

@router.post("/runtime/ssh-bruteforce/scroll")
@router.post("/runtime/single/scroll")
@router.post("/runtime/dual/scroll")
async def runtime_scroll_ssh_bruteforce(direction: str = "up"):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, guac_autosolve.scroll_terminal, "cyber_attacker_kali", direction)
    return {"success": True}

@router.post("/runtime/metasploit/scroll")
async def runtime_scroll_metasploit(direction: str = "up"):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, guac_autosolve.scroll_terminal, "cyber_kali_msf", direction)
    return {"success": True}
