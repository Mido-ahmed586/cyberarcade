"""
seed_certificates.py
--------------------
Backfill certificates for every (user, course) pair where all course tasks
have been answered correctly.  Safe to run multiple times — skips pairs that
already have a certificate (enforced by the unique constraint on the table).

Usage:
    cd cyberarcade-backend
    .\.venv\Scripts\python.exe seed_certificates.py
"""

import asyncio
import sys
from pathlib import Path

# Make sure app imports resolve from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import select, func
from app.core.database import async_session, engine, Base
from app.models.user import User
from app.models.course import Course
from app.models.lab import Lab, LabTask
from app.models.lab_instance import LabProgress
from app.models.certificate import Certificate
from app.services.certificate_service import generate_certificate, check_course_completion

# Register all models so create_all works
import app.models  # noqa: F401


async def _ensure_table():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed():
    await _ensure_table()

    async with async_session() as db:
        # Load all published courses that have at least one task
        courses_res = await db.execute(
            select(Course)
            .join(Lab, Lab.course_id == Course.course_id)
            .join(LabTask, LabTask.lab_id == Lab.lab_id)
            .where(Course.is_published == True)  # noqa: E712
            .distinct()
        )
        courses = list(courses_res.scalars().all())

        if not courses:
            print("No published courses with tasks found.")
            return

        # Load all active students
        users_res = await db.execute(
            select(User).where(User.is_active == True)  # noqa: E712
        )
        users = list(users_res.scalars().all())

        print(f"Checking {len(courses)} course(s) × {len(users)} user(s) …\n")

        generated = 0
        skipped   = 0

        for course in courses:
            for user in users:
                is_complete, total, correct = await check_course_completion(
                    db, user.user_id, course.course_id
                )
                if not is_complete or total == 0:
                    continue

                # Already has a cert?
                existing_res = await db.execute(
                    select(Certificate)
                    .where(Certificate.user_id == user.user_id)
                    .where(Certificate.course_id == course.course_id)
                )
                if existing_res.scalar_one_or_none():
                    print(f"  SKIP  {user.full_name:<28} | {course.title}")
                    skipped += 1
                    continue

                cert = await generate_certificate(
                    db=db,
                    user_id=user.user_id,
                    course_id=course.course_id,
                    student_name=user.full_name,
                    course_name=course.title,
                )
                print(f"  CERT  {user.full_name:<28} | {course.title:<40} | {cert.serial_number}")
                generated += 1

        await db.commit()

    print(f"\n{'='*60}")
    print(f"  Generated : {generated}")
    print(f"  Skipped   : {skipped}  (already existed)")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(seed())
