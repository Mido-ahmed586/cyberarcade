"""
patch_lab6_autosolve.py — Fixes autosolve_commands for Lab 6 Tasks 6, 7, 8.

Run from the cyberarcade-backend directory:
    python patch_lab6_autosolve.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, update
from app.core.database import async_session
from app.models.lab import Lab, LabTask

LABS_PATCHES: dict[str, dict[str, list[str]]] = {
    "Steganography and Metadata Analysis": {
        "Task 5 - Evidence: Embedded Filename": [
            "cd ~/labs/insider",
            "steghide info -p 'forensics' company_logo.bmp",
        ],
        "Task 6 - Evidence: USB Serial Number": [
            'steghide extract -sf company_logo.bmp -p "forensics"',
            "cat hidden_evidence.txt",
        ],
        "Task 7 - Evidence: Contact Email": [
            "cat hidden_evidence.txt",
        ],
        "Task 8 - Evidence: Files Copied to USB": [
            "cat hidden_evidence.txt | grep -i copied",
        ],
        "Task 9 - Evidence: Disguised File Type": [
            "exiftool -FileType financial_report.docx",
        ],
    },
    "Malware Persistence Analysis": {
        "Task 5 - Evidence: Cron Backdoor Script": [
            "cd ~/labs/malware",
            "crontab -l",
        ],
        "Task 6 - Evidence: Decoded Payload Command": [
            "base64 -d encoded_payload.txt",
        ],
        "Task 7 - Evidence: Backdoor Username": [
            "cat /etc/passwd | grep -v nologin | grep -v false",
        ],
        "Task 8 - Evidence: Attacker IP Address": [
            'grep "Accepted" auth.log',
        ],
        "Task 9 - Evidence: Login Username": [
            'grep "Accepted" auth.log',
        ],
    },
}


async def patch():
    async with async_session() as db:
        total = 0
        for lab_title, patches in LABS_PATCHES.items():
            lab_result = await db.execute(select(Lab).where(Lab.title == lab_title))
            lab = lab_result.scalar_one_or_none()
            if not lab:
                print(f"[error] Lab not found: '{lab_title}' — skipping")
                continue

            print(f"[ok] Found lab: {lab.title} (id={lab.lab_id})")

            tasks_result = await db.execute(
                select(LabTask).where(LabTask.lab_id == lab.lab_id)
            )
            tasks = tasks_result.scalars().all()

            for task in tasks:
                if task.title in patches:
                    await db.execute(
                        update(LabTask)
                        .where(LabTask.task_id == task.task_id)
                        .values(autosolve_commands=patches[task.title])
                    )
                    print(f"  [patched] {task.title}")
                    total += 1

        await db.commit()
        print(f"\n[done] {total} task(s) updated.")


if __name__ == "__main__":
    asyncio.run(patch())
