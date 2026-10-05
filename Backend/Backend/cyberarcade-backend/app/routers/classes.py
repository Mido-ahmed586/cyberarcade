import secrets
import string
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from uuid import UUID
from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.models.course import Course
from app.models.lab import Lab
from app.models.class_group import Class, ClassEnrollment
from app.models.lab_instance import LabProgress
from app.schemas.class_group import (
    ClassCreate,
    ClassResponse,
    JoinClassRequest,
    EnrollmentResponse,
    StudentProgressReport,
)

router = APIRouter(prefix="/api/classes", tags=["Classes"])


def generate_class_code() -> str:
    chars = string.ascii_uppercase + string.digits
    random_part = "".join(secrets.choice(chars) for _ in range(6))
    return f"CYBER-{random_part}"


@router.post("", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    req: ClassCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin", "system_admin")),
):
    """Create a new class (instructor only)."""
    result = await db.execute(select(Course).where(Course.course_id == req.course_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Course not found")

    class_code = generate_class_code()
    while True:
        existing = await db.execute(select(Class).where(Class.class_code == class_code))
        if not existing.scalar_one_or_none():
            break
        class_code = generate_class_code()

    new_class = Class(
        class_code=class_code,
        instructor_id=current_user.user_id,
        course_id=req.course_id,
        name=req.name,
        description=req.description,
        max_students=req.max_students,
    )
    db.add(new_class)
    await db.flush()
    await db.refresh(new_class)

    return ClassResponse(
        class_id=new_class.class_id,
        class_code=new_class.class_code,
        name=new_class.name,
        description=new_class.description,
        course_id=new_class.course_id,
        instructor_id=new_class.instructor_id,
        max_students=new_class.max_students,
        is_active=new_class.is_active,
        created_at=new_class.created_at,
        student_count=0,
    )


@router.get("/my-classes", response_model=list[ClassResponse])
async def list_my_classes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin", "system_admin")),
):
    """List classes created by the current instructor."""
    result = await db.execute(
        select(Class)
        .where(Class.instructor_id == current_user.user_id)
        .order_by(Class.created_at.desc())
    )
    classes = result.scalars().all()

    response = []
    for cls in classes:
        count_result = await db.execute(
            select(func.count(ClassEnrollment.enrollment_id))
            .where(ClassEnrollment.class_id == cls.class_id)
        )
        student_count = count_result.scalar()
        response.append(
            ClassResponse(
                class_id=cls.class_id,
                class_code=cls.class_code,
                name=cls.name,
                description=cls.description,
                course_id=cls.course_id,
                instructor_id=cls.instructor_id,
                max_students=cls.max_students,
                is_active=cls.is_active,
                created_at=cls.created_at,
                student_count=student_count,
            )
        )
    return response


@router.get("/{class_id}/progress", response_model=list[StudentProgressReport])
async def get_class_progress(
    class_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin", "system_admin")),
):
    """Get progress report for all students in a class."""
    result = await db.execute(select(Class).where(Class.class_id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    if cls.instructor_id != current_user.user_id and current_user.role not in ("admin", "system_admin"):
        raise HTTPException(status_code=403, detail="Not your class")

    enrollments_result = await db.execute(
        select(ClassEnrollment)
        .options(selectinload(ClassEnrollment.student))
        .where(ClassEnrollment.class_id == class_id)
    )
    enrollments = enrollments_result.scalars().all()

    lab_ids_result = await db.execute(
        select(Lab.lab_id).where(Lab.course_id == cls.course_id)
    )
    lab_ids = [row[0] for row in lab_ids_result.all()]

    reports = []
    for enrollment in enrollments:
        student = enrollment.student

        if lab_ids:
            progress_result = await db.execute(
                select(LabProgress).where(
                    LabProgress.user_id == student.user_id,
                    LabProgress.lab_id.in_(lab_ids),
                )
            )
            progress_records = progress_result.scalars().all()
        else:
            progress_records = []

        reports.append(
            StudentProgressReport(
                student_id=student.user_id,
                student_name=student.full_name,
                tasks_completed=sum(1 for p in progress_records if p.status == "completed"),
                tasks_auto_solved=sum(1 for p in progress_records if p.status == "auto_solved"),
                total_tasks_attempted=len(progress_records),
                total_hints_used=sum(p.hints_used for p in progress_records),
            )
        )

    return reports


@router.post("/join", response_model=EnrollmentResponse)
async def join_class(
    req: JoinClassRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Join a class using a class code."""
    result = await db.execute(
        select(Class).where(Class.class_code == req.class_code, Class.is_active == True)
    )
    cls = result.scalar_one_or_none()

    if not cls:
        raise HTTPException(status_code=404, detail="Invalid or inactive class code")

    existing = await db.execute(
        select(ClassEnrollment).where(
            ClassEnrollment.class_id == cls.class_id,
            ClassEnrollment.student_id == current_user.user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already enrolled in this class")

    if cls.max_students:
        count_result = await db.execute(
            select(func.count(ClassEnrollment.enrollment_id))
            .where(ClassEnrollment.class_id == cls.class_id)
        )
        if count_result.scalar() >= cls.max_students:
            raise HTTPException(status_code=409, detail="Class is full")

    enrollment = ClassEnrollment(class_id=cls.class_id, student_id=current_user.user_id)
    db.add(enrollment)
    await db.flush()
    await db.refresh(enrollment)
    return enrollment


@router.get("/enrolled", response_model=list[ClassResponse])
async def list_enrolled_classes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all classes the current student is enrolled in."""
    result = await db.execute(
        select(ClassEnrollment)
        .options(selectinload(ClassEnrollment.class_group))
        .where(ClassEnrollment.student_id == current_user.user_id)
    )
    enrollments = result.scalars().all()

    response = []
    for enrollment in enrollments:
        cls = enrollment.class_group
        count_result = await db.execute(
            select(func.count(ClassEnrollment.enrollment_id))
            .where(ClassEnrollment.class_id == cls.class_id)
        )
        response.append(
            ClassResponse(
                class_id=cls.class_id,
                class_code=cls.class_code,
                name=cls.name,
                description=cls.description,
                course_id=cls.course_id,
                instructor_id=cls.instructor_id,
                max_students=cls.max_students,
                is_active=cls.is_active,
                created_at=cls.created_at,
                student_count=count_result.scalar(),
            )
        )
    return response
