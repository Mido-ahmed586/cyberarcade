# CyberArcade — Full Stack

This folder contains the wired-together frontend and backend for CyberArcade.

```
Web/
├── Backend/Backend/cyberarcade-backend/     FastAPI + PostgreSQL + JWT auth
└── Frontend/Frontend/cyberarcade/           React + Vite frontend
```

## Run order

1. **Database** — make sure the PostgreSQL `cyberarcade` database is up and the
   schema is applied (see backend README).
2. **Backend** — from `Backend/Backend/cyberarcade-backend`:
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```
   Backend listens on `http://127.0.0.1:8000` with Swagger at `/docs`.
3. **Frontend** — from `Frontend/Frontend/cyberarcade`:
   ```bash
   npm install
   npm run dev
   ```
   Frontend listens on `http://localhost:5173`. It's already in the backend's
   `ALLOWED_ORIGINS`, so CORS works without changes.

## What was wired up

The frontend was originally running on mocks. It now speaks to the real
backend across every flow:

- Register / login / token-refresh / logout against `/api/auth/*`
- Course list, detail, and labs against `/api/courses/*`
- Lab tasks, server-gated hints (with live countdown), answer submission, and
  auto-solve against `/api/labs/*`
- Chatbot messages and history against `/api/chatbot/*`
- JWTs persist across page reloads (localStorage) with automatic refresh on
  401 responses

One backend endpoint was added to support the course-detail page:
`GET /api/courses/{course_id}/labs` — lists published labs in a course.

## Empty-database note

The backend starts with no courses. See the frontend README for the checklist
to seed a user, promote it to admin, and create a course + lab + tasks
through Swagger.

## Known backend TODOs (from the original backend README)

- Docker orchestrator for attacker/victim containers — lab start/stop is
  already called by the frontend, but no containers are provisioned yet.
- Guacamole connection for the live VM terminal — the lab page shows instance
  metadata in the meantime.
- LLM integration in `app/services/ai_service.py` — the chatbot endpoint
  currently echoes your question.

None of these block the frontend from running; they just mean certain panels
are placeholders until the backend side is implemented.
