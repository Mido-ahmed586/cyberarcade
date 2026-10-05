from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from typing import Optional
from app.core.database import get_db
from app.core.security import require_role
from app.models.user import User
from app.models.course import Course
from app.models.lab import Lab
from app.models.lab_instance import LabInstance
from app.models.class_group import Class, ClassEnrollment
from app.models.chatbot import AuditLog
from app.schemas.admin import (
    AdminStatsResponse,
    UserAdminResponse,
    RoleUpdateRequest,
    StatusUpdateRequest,
    AuditLogResponse,
)
from app.schemas.auth import MessageResponse

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "system_admin")),
):
    """Get platform-wide statistics."""
    total_users = (await db.execute(select(func.count(User.user_id)))).scalar()
    active_users = (await db.execute(
        select(func.count(User.user_id)).where(User.is_active == True)
    )).scalar()
    total_courses = (await db.execute(select(func.count(Course.course_id)))).scalar()
    published_courses = (await db.execute(
        select(func.count(Course.course_id)).where(Course.is_published == True)
    )).scalar()
    total_labs = (await db.execute(select(func.count(Lab.lab_id)))).scalar()
    active_lab_instances = (await db.execute(
        select(func.count(LabInstance.instance_id))
        .where(LabInstance.status.in_(["starting", "running", "paused"]))
    )).scalar()
    total_classes = (await db.execute(select(func.count(Class.class_id)))).scalar()
    total_enrollments = (await db.execute(
        select(func.count(ClassEnrollment.enrollment_id))
    )).scalar()

    return AdminStatsResponse(
        total_users=total_users,
        active_users=active_users,
        total_courses=total_courses,
        published_courses=published_courses,
        total_labs=total_labs,
        active_lab_instances=active_lab_instances,
        total_classes=total_classes,
        total_enrollments=total_enrollments,
    )


@router.get("/users", response_model=list[UserAdminResponse])
async def list_users(
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "system_admin")),
):
    """List users with optional filters."""
    query = select(User)
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/users/{user_id}", response_model=UserAdminResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "system_admin")),
):
    """Get user detail."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{user_id}/role", response_model=MessageResponse)
async def update_user_role(
    user_id: UUID,
    req: RoleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "system_admin")),
):
    """Change a user's role."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = user.role
    user.role = req.role

    log = AuditLog(
        user_id=current_user.user_id,
        action="user.role_change",
        target_type="user",
        target_id=user_id,
        metadata_={"old_role": old_role, "new_role": req.role},
    )
    db.add(log)

    return MessageResponse(message=f"User role updated to {req.role}")


@router.put("/users/{user_id}/status", response_model=MessageResponse)
async def update_user_status(
    user_id: UUID,
    req: StatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "system_admin")),
):
    """Activate or deactivate a user."""
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = req.is_active

    log = AuditLog(
        user_id=current_user.user_id,
        action="user.status_change",
        target_type="user",
        target_id=user_id,
        metadata_={"is_active": req.is_active},
    )
    db.add(log)

    return MessageResponse(message=f"User {'activated' if req.is_active else 'deactivated'}")


@router.get("/audit-log", response_model=list[AuditLogResponse])
async def get_audit_log(
    action: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "system_admin")),
):
    """View audit trail."""
    query = select(AuditLog)
    if action:
        query = query.where(AuditLog.action == action)
    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    return result.scalars().all()
