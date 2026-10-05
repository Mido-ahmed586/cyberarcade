#!/bin/bash
# Docker container entrypoint — runs on every container start.
# Order: wait for DB → create tables + seed → stamp Alembic → start uvicorn
set -e

# ── 1. Wait for PostgreSQL ───────────────────────────────────────────────────
echo "[init] Waiting for PostgreSQL..."
python - << 'PYEOF'
import asyncio, asyncpg, os, sys

async def wait():
    raw = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
    for i in range(30):
        try:
            conn = await asyncpg.connect(raw)
            await conn.close()
            print("[init] PostgreSQL is ready.")
            return
        except Exception as exc:
            print(f"[init] Waiting ({i+1}/30): {exc}")
            await asyncio.sleep(2)
    print("[init] ERROR: PostgreSQL not reachable after 60 s")
    sys.exit(1)

asyncio.run(wait())
PYEOF

# ── 2. Create tables and seed all courses (idempotent) ───────────────────────
echo "[init] Running seed_all..."
python seeds/seed_all.py

# ── 3. Stamp Alembic so future `alembic upgrade head` migrations work ────────
# alembic stamp head is safe to run multiple times — only stamps if not already set
echo "[init] Stamping Alembic revision..."
alembic stamp head

# ── 4. Start the API server ──────────────────────────────────────────────────
echo "[init] Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
