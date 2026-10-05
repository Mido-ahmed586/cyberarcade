# CyberArcade full project

This package contains the working project source:

- `Frontend/Frontend/cyberarcade` - React/Vite frontend
- `Backend/Backend/cyberarcade-backend` - FastAPI backend
- `scenarios` - Docker lab/terminal stacks

Generated/private folders are intentionally not included:

- `node_modules`
- Python `venv` / `.venv`
- `.env` files with secrets
- frontend `dist`
- Python cache files

## Setup

### Backend

```bash
cd Backend/Backend/cyberarcade-backend
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install greenlet email-validator paramiko
```

The backend `.env` is already included and uses the shared PostgreSQL password
`cyberarcade`:

```env
DATABASE_URL=postgresql+asyncpg://cyberarcade_admin:cyberarcade@localhost:5432/cyberarcade
```

Start Docker Desktop, then run:

```bash
env -u DEBUG .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd Frontend/Frontend/cyberarcade
npm install
```

The frontend `.env` is already included and points to `http://127.0.0.1:8000`.

Then run:

```bash
npm run dev -- --host 127.0.0.1 --port 5173
```

Open:

```text
http://127.0.0.1:5173
```

## Notes

- The lab terminal uses Docker and Apache Guacamole on port `8081`.
- If Docker is not running, Start Lab and Auto-Solve will fail.
- If Guacamole asks for credentials, use `student` / `student123`.
