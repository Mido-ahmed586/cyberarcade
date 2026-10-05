"""Delete the existing DF course and re-seed it fresh."""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sqlalchemy import text
from app.core.database import async_session

async def main():
    async with async_session() as db:
        res = await db.execute(text(
            "DELETE FROM courses WHERE title='Digital Forensics' RETURNING course_id, title"
        ))
        rows = res.fetchall()
        if rows:
            print(f"Deleted: {rows[0][1]} ({rows[0][0]})")
        else:
            print("No DF course found to delete.")
        await db.commit()
        print("Done — now run: python seed_df_course.py")

asyncio.run(main())
