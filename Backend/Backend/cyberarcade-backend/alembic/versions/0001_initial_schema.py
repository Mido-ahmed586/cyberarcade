"""Initial schema baseline

Revision ID: 0001
Revises:
Create Date: 2026-05-27

NOTE: Tables are created by SQLAlchemy's create_all() called in seeds/seed_all.py
(and again via the FastAPI lifespan in app/main.py in DEBUG mode).
This migration is intentionally a no-op upgrade so Alembic can track the
baseline state.  Future schema changes should be generated with:

    alembic revision --autogenerate -m "describe your change"

"""
from typing import Sequence, Union

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tables are managed by create_all() for initial setup.
    pass


def downgrade() -> None:
    # Intentionally left empty — dropping all tables should be done deliberately
    # (e.g. docker-compose down -v) rather than via an automatic migration.
    pass
