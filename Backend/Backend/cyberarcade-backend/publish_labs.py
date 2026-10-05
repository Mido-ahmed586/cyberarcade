"""Quick fix: publish all seeded labs."""
import asyncio, sys
sys.path.insert(0, ".")

async def publish_labs():
    from app.core.database import async_session
    from app.models.lab import Lab
    from sqlalchemy import update

    async with async_session() as db:
        result = await db.execute(
            update(Lab).where(Lab.is_published == False).values(is_published=True)
        )
        await db.commit()
        print(f"Published {result.rowcount} labs!")

asyncio.run(publish_labs())
