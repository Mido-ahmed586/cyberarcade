"""
import_course.py
----------------
Import courses exported by export_course.py.
Safe to re-run — skips courses that already exist (matched by title).

Usage (run from cyberarcade-backend folder):
    .\.venv\Scripts\python.exe import_course.py course_export.json
    .\.venv\Scripts\python.exe import_course.py forensics.json
"""

import asyncio, json, sys, uuid
from pathlib import Path
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parent))

import app.models  # noqa: F401
from app.core.database import async_session, engine, Base
from app.models.course import Course
from app.models.lab import Lab, LabTask, Hint
from app.models.user import User


async def _ensure_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _get_admin_id(db) -> uuid.UUID:
    """Return the first admin/system_admin user id to use as created_by."""
    res = await db.execute(
        select(User.user_id).where(User.role.in_(["admin", "system_admin"])).limit(1)
    )
    uid = res.scalar_one_or_none()
    if uid:
        return uid
    # Fall back to any user
    res2 = await db.execute(select(User.user_id).limit(1))
    uid2 = res2.scalar_one_or_none()
    if uid2:
        return uid2
    raise RuntimeError("No users found in the database. Create an admin account first.")


async def import_courses(in_path: Path):
    if not in_path.exists():
        print(f"File not found: {in_path}")
        sys.exit(1)

    payload = json.loads(in_path.read_text(encoding="utf-8"))
    await _ensure_tables()

    async with async_session() as db:
        admin_id = await _get_admin_id(db)
        imported = skipped = 0

        for c in payload:
            # Skip if a course with the same title already exists
            existing = (await db.execute(
                select(Course).where(Course.title == c["title"])
            )).scalar_one_or_none()

            if existing:
                print(f"  SKIP  already exists: {c['title']}")
                skipped += 1
                continue

            course = Course(
                course_id=uuid.UUID(c["course_id"]),
                title=c["title"],
                description=c.get("description") or "",
                difficulty_level=c.get("difficulty_level") or "beginner",
                category=c.get("category") or "General",
                estimated_hours=c.get("estimated_hours"),
                is_published=c.get("is_published", True),
                created_by=admin_id,
            )
            db.add(course)
            await db.flush()

            for idx, l in enumerate(c.get("labs", [])):
                lab = Lab(
                    lab_id=uuid.UUID(l["lab_id"]),
                    course_id=course.course_id,
                    title=l["title"],
                    description=l.get("description") or "",
                    difficulty=l.get("difficulty") or "medium",
                    docker_compose_config=l.get("docker_compose_config") or {},
                    has_auto_solve=l.get("has_auto_solve", False),
                    max_duration_minutes=l.get("max_duration_minutes", 120),
                    sort_order=l.get("sort_order", idx),
                    is_published=l.get("is_published", True),
                )
                db.add(lab)
                await db.flush()

                for tidx, t in enumerate(l.get("tasks", [])):
                    task = LabTask(
                        task_id=uuid.UUID(t["task_id"]),
                        lab_id=lab.lab_id,
                        title=t["title"],
                        instructions=t.get("instructions") or "",
                        expected_answer=t.get("expected_answer"),
                        autosolve_commands=t.get("autosolve_commands") or [],
                        sort_order=t.get("sort_order", tidx),
                    )
                    db.add(task)
                    await db.flush()

                    for h in t.get("hints", []):
                        hint = Hint(
                            hint_id=uuid.UUID(h["hint_id"]),
                            task_id=task.task_id,
                            hint_text=h.get("hint_text") or "",
                            hint_order=h.get("hint_order", 0),
                            delay_minutes=h.get("delay_minutes", 5),
                        )
                        db.add(hint)

            await db.flush()
            task_count = sum(len(l.get("tasks", [])) for l in c.get("labs", []))
            print(f"  IMPORT  {c['title']}  ({len(c.get('labs', []))} labs, {task_count} tasks)")
            imported += 1

        await db.commit()

    print(f"\n{'='*50}")
    print(f"  Imported : {imported}")
    print(f"  Skipped  : {skipped}  (already existed)")
    print(f"{'='*50}")
    if imported:
        print("\nRestart the backend server to see the new course(s).")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: .venv\\Scripts\\python.exe import_course.py <export_file.json>")
        sys.exit(1)
    asyncio.run(import_courses(Path(sys.argv[1])))
