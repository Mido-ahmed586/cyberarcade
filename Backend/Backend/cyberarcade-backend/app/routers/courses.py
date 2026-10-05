from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.models.course import Course, Module
from app.models.lab import Lab
from app.schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseDetailResponse,
    ModuleCreate,
    ModuleUpdate,
    ModuleResponse,
)
from app.models.lab_instance import LabInstance, LabProgress
from app.schemas.lab import LabResponse, CourseProgressResponse
from app.schemas.auth import MessageResponse

router = APIRouter(prefix="/api/courses", tags=["Courses"])


@router.get("", response_model=list[CourseResponse])
async def list_courses(
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(12, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """List published courses with optional filters."""
    query = select(Course).where(Course.is_published == True)

    if category:
        query = query.where(Course.category == category)
    if difficulty:
        query = query.where(Course.difficulty_level == difficulty)

    query = query.order_by(Course.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{course_id}", response_model=CourseDetailResponse)
async def get_course(course_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get course detail with modules."""
    result = await db.execute(
        select(Course)
        .options(selectinload(Course.modules))
        .where(Course.course_id == course_id, Course.is_published == True)
    )
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    lab_count_result = await db.execute(
        select(func.count(Lab.lab_id))
        .where(Lab.course_id == course_id, Lab.is_published == True)
    )
    lab_count = lab_count_result.scalar()

    return CourseDetailResponse(
        course_id=course.course_id,
        title=course.title,
        description=course.description,
        difficulty_level=course.difficulty_level,
        category=course.category,
        estimated_hours=course.estimated_hours,
        is_published=course.is_published,
        created_at=course.created_at,
        updated_at=course.updated_at,
        modules=course.modules,
        lab_count=lab_count,
    )


@router.get("/{course_id}/my-progress", response_model=CourseProgressResponse)
async def get_course_progress(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return per-lab completion status and overall progress % for the current user."""
    from app.models.lab import LabTask

    # Verify course exists
    course_result = await db.execute(
        select(Course).where(Course.course_id == course_id, Course.is_published == True)
    )
    if not course_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found")

    # Get all published labs
    labs_result = await db.execute(
        select(Lab).where(Lab.course_id == course_id, Lab.is_published == True)
        .order_by(Lab.sort_order.asc())
    )
    labs = labs_result.scalars().all()
    total_labs = len(labs)

    if total_labs == 0:
        return CourseProgressResponse(
            course_id=course_id,
            completed_labs=0,
            total_labs=0,
            percent=0,
            lab_statuses={},
        )

    lab_ids = [lab.lab_id for lab in labs]

    # Count total tasks per lab and completed tasks per lab for this user
    tasks_result = await db.execute(
        select(LabTask.lab_id, func.count(LabTask.task_id).label("total"))
        .where(LabTask.lab_id.in_(lab_ids))
        .group_by(LabTask.lab_id)
    )
    tasks_by_lab = {row.lab_id: row.total for row in tasks_result}

    progress_result = await db.execute(
        select(LabProgress.lab_id, func.count(LabProgress.progress_id).label("done"))
        .where(
            LabProgress.user_id == current_user.user_id,
            LabProgress.lab_id.in_(lab_ids),
            LabProgress.status.in_(["completed", "auto_solved"]),
        )
        .group_by(LabProgress.lab_id)
    )
    completed_by_lab = {row.lab_id: row.done for row in progress_result}

    any_progress_result = await db.execute(
        select(LabProgress.lab_id)
        .where(
            LabProgress.user_id == current_user.user_id,
            LabProgress.lab_id.in_(lab_ids),
        )
        .group_by(LabProgress.lab_id)
    )
    touched_lab_ids = {row[0] for row in any_progress_result.all()}

    instance_result = await db.execute(
        select(LabInstance.lab_id)
        .where(
            LabInstance.user_id == current_user.user_id,
            LabInstance.lab_id.in_(lab_ids),
        )
        .group_by(LabInstance.lab_id)
    )
    touched_lab_ids.update(row[0] for row in instance_result.all())

    lab_statuses = {}
    completed_labs = 0
    for lab in labs:
        total_tasks = tasks_by_lab.get(lab.lab_id, 0)
        done_tasks = completed_by_lab.get(lab.lab_id, 0)
        if total_tasks == 0:
            lab_statuses[str(lab.lab_id)] = "not_started"
        elif done_tasks >= total_tasks:
            lab_statuses[str(lab.lab_id)] = "completed"
            completed_labs += 1
        elif done_tasks > 0 or lab.lab_id in touched_lab_ids:
            lab_statuses[str(lab.lab_id)] = "in_progress"
        else:
            lab_statuses[str(lab.lab_id)] = "not_started"

    percent = round(completed_labs / total_labs * 100) if total_labs else 0
    return CourseProgressResponse(
        course_id=course_id,
        completed_labs=completed_labs,
        total_labs=total_labs,
        percent=percent,
        lab_statuses=lab_statuses,
    )


@router.get("/{course_id}/labs", response_model=list[LabResponse])
async def list_course_labs(course_id: UUID, db: AsyncSession = Depends(get_db)):
    """List all published labs belonging to a course."""
    course_check = await db.execute(
        select(Course).where(Course.course_id == course_id, Course.is_published == True)
    )
    if not course_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found")

    result = await db.execute(
        select(Lab)
        .where(Lab.course_id == course_id, Lab.is_published == True)
        .order_by(Lab.sort_order.asc(), Lab.created_at.asc())
    )
    return result.scalars().all()


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    req: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "system_admin")),
):
    """Create a course (admin only)."""
    course = Course(**req.model_dump(), created_by=current_user.user_id)
    db.add(course)
    await db.flush()
    await db.refresh(course)
    return course


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: UUID,
    req: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "system_admin")),
):
    """Update a course (admin only)."""
    result = await db.execute(select(Course).where(Course.course_id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(course, field, value)

    await db.flush()
    await db.refresh(course)
    return course


@router.delete("/{course_id}", response_model=MessageResponse)
async def delete_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "system_admin")),
):
    """Delete a course (admin only)."""
    result = await db.execute(select(Course).where(Course.course_id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    await db.delete(course)
    return MessageResponse(message="Course deleted successfully")


@router.post("/{course_id}/modules", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED)
async def create_module(
    course_id: UUID,
    req: ModuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "system_admin")),
):
    """Add a module to a course (admin only)."""
    result = await db.execute(select(Course).where(Course.course_id == course_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found")

    module = Module(course_id=course_id, **req.model_dump())
    db.add(module)
    await db.flush()
    await db.refresh(module)
    return module


@router.put("/{course_id}/modules/{module_id}", response_model=ModuleResponse)
async def update_module(
    course_id: UUID,
    module_id: UUID,
    req: ModuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "system_admin")),
):
    """Update a module (admin only)."""
    result = await db.execute(
        select(Module).where(Module.module_id == module_id, Module.course_id == course_id)
    )
    module = result.scalar_one_or_none()

    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(module, field, value)

    await db.flush()
    await db.refresh(module)
    return module
