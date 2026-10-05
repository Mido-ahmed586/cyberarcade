"""
export_course.py
----------------
Export one or more courses (with all labs, tasks, hints) to a JSON file.

Usage (run from cyberarcade-backend folder):
    .\.venv\Scripts\python.exe export_course.py
    .\.venv\Scripts\python.exe export_course.py "Digital Forensics"
    .\.venv\Scripts\python.exe export_course.py "Digital Forensics" --out forensics.json
"""

import asyncio, json, sys
from pathlib import Path
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parent))

import app.models  # noqa: F401  – register all models
from app.core.database import async_session
from app.models.course import Course
from app.models.lab import Lab, LabTask, Hint


def _s(v):
    return str(v) if v is not None else None


async def export_courses(search: str | None, out_path: Path):
    async with async_session() as db:
        q = select(Course)
        if search:
            q = q.where(Course.title.ilike(f"%{search}%"))
        courses = (await db.execute(q)).scalars().all()

        if not courses:
            print(f"No courses found{f' matching {search!r}' if search else ''}.")
            return

        payload = []
        for course in courses:
            labs = (await db.execute(
                select(Lab).where(Lab.course_id == course.course_id).order_by(Lab.sort_order)
            )).scalars().all()

            labs_data = []
            for lab in labs:
                tasks = (await db.execute(
                    select(LabTask).where(LabTask.lab_id == lab.lab_id).order_by(LabTask.sort_order)
                )).scalars().all()

                tasks_data = []
                for task in tasks:
                    hints = (await db.execute(
                        select(Hint).where(Hint.task_id == task.task_id).order_by(Hint.hint_order)
                    )).scalars().all()

                    tasks_data.append({
                        "task_id": _s(task.task_id),
                        "title": task.title,
                        "instructions": task.instructions,
                        "expected_answer": task.expected_answer,
                        "autosolve_commands": task.autosolve_commands or [],
                        "sort_order": task.sort_order,
                        "hints": [
                            {
                                "hint_id": _s(h.hint_id),
                                "hint_text": h.hint_text,
                                "hint_order": h.hint_order,
                                "delay_minutes": h.delay_minutes,
                            }
                            for h in hints
                        ],
                    })

                labs_data.append({
                    "lab_id": _s(lab.lab_id),
                    "title": lab.title,
                    "description": lab.description,
                    "difficulty": lab.difficulty,
                    "docker_compose_config": lab.docker_compose_config,
                    "has_auto_solve": lab.has_auto_solve,
                    "max_duration_minutes": lab.max_duration_minutes,
                    "sort_order": lab.sort_order,
                    "is_published": lab.is_published,
                    "tasks": tasks_data,
                })

            payload.append({
                "course_id": _s(course.course_id),
                "title": course.title,
                "description": course.description,
                "difficulty_level": course.difficulty_level,
                "category": course.category,
                "estimated_hours": float(course.estimated_hours) if course.estimated_hours else None,
                "is_published": course.is_published,
                "labs": labs_data,
            })

        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nExported {len(payload)} course(s) -> {out_path}")
        for c in payload:
            task_count = sum(len(l["tasks"]) for l in c["labs"])
            print(f"  • {c['title']}  ({len(c['labs'])} labs, {task_count} tasks)")
        print(f"\nSend the file  {out_path}  to your friend.")


if __name__ == "__main__":
    args  = [a for a in sys.argv[1:] if not a.startswith("--")]
    out_f = next((sys.argv[i+1] for i, a in enumerate(sys.argv) if a == "--out"), None)
    search   = args[0] if args else None
    out_path = Path(out_f) if out_f else Path("course_export.json")
    asyncio.run(export_courses(search, out_path))
