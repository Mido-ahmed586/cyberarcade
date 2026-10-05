"""Fix has_auto_solve flag and verify autosolve_commands for DF labs."""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sqlalchemy import text
from app.core.database import async_session

async def main():
    async with async_session() as db:
        res = await db.execute(text(
            "UPDATE labs SET has_auto_solve=true "
            "WHERE course_id=(SELECT course_id FROM courses WHERE title='Digital Forensics') "
            "AND (docker_compose_config->>'runtime_slug')='df-kali' "
            "RETURNING lab_id, title, has_auto_solve"
        ))
        rows = res.fetchall()
        print(f"Updated {len(rows)} labs:")
        for r in rows:
            print(f"  {r[1]} -> has_auto_solve={r[2]}")

        r2 = await db.execute(text(
            "SELECT t.title, jsonb_array_length(t.autosolve_commands) as cmd_count "
            "FROM lab_tasks t "
            "JOIN labs l ON l.lab_id=t.lab_id "
            "JOIN courses c ON c.course_id=l.course_id "
            "WHERE c.title='Digital Forensics' AND l.sort_order=1 "
            "ORDER BY t.sort_order"
        ))
        print("\nLab 1 tasks (autosolve command count):")
        for row in r2.fetchall():
            print(f"  {row[0][:60]}: {row[1]} cmds")

        await db.commit()
        print("\nDone.")

asyncio.run(main())
