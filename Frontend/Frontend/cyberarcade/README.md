# CyberArcade Frontend — React + Vite

This is the React frontend for CyberArcade, wired to the FastAPI backend in
`../../../Backend/Backend/cyberarcade-backend`.

## How it's wired

- `src/services/api.js` — axios client. Reads the backend URL from
  `VITE_API_URL`, attaches the JWT access token from `localStorage` to every
  request, and transparently refreshes it on a 401 using the stored refresh
  token. If the refresh fails, tokens are cleared and the user is dropped back
  to the landing page.
- `src/services/auth.service.js` — `/api/auth/*` (register, login, me, logout)
- `src/services/courses.service.js` — `/api/courses/*`
- `src/services/labs.service.js` — `/api/labs/*` (detail, start, stop, submit, hint, auto-solve)
- `src/services/chat.service.js` — `/api/chatbot/*`
- `src/hooks/useAuth.js` — on mount, if a token is in `localStorage` it calls
  `/api/auth/me` to rehydrate the session before the app is shown.

The pages (`Courses`, `CourseDetail`, `Dashboard`, `Lab`, `Chat`, `Auth`) all
call those services — no mocks remain.

## Setup

### 1. Prerequisites

- **Node.js 18+** — https://nodejs.org
- The CyberArcade backend running (see the backend README).

### 2. Configure the backend URL

Copy `.env.example` to `.env` and adjust only if your backend is not on
`http://127.0.0.1:8000`:

```
VITE_API_URL=http://127.0.0.1:8000
```

### 3. Install and run

```bash
npm install
npm run dev
```

Vite will start on `http://localhost:5173`. That origin is already in the
backend's `ALLOWED_ORIGINS`, so CORS will work out of the box.

## First-run checklist

Because the backend ships with an empty database, the UI will initially show
"No published courses yet." To see content:

1. Start the backend (`uvicorn app.main:app --reload --port 8000`).
2. Register a user through the frontend (or via `/docs`).
3. In `pgAdmin`, promote yourself to admin:
   ```sql
   UPDATE users SET role = 'system_admin' WHERE email = 'you@example.com';
   ```
4. Log out and back in so the new role is in your JWT.
5. Use Swagger at `http://127.0.0.1:8000/docs` to `POST /api/courses`, then
   `POST /api/labs`, then `POST /api/labs/{lab_id}/tasks`, and optionally
   `POST /api/labs/{lab_id}/tasks/{task_id}/hints`. Make sure
   `is_published: true` on courses and labs or they won't appear.
6. Refresh the frontend — the courses should now render.

## Notes on what the backend doesn't do yet

- **VM panel on the lab page** — the backend has TODOs for the Docker
  orchestrator and Guacamole integration. Until those are wired in, the VM
  panel shows the instance metadata (status, expiry, etc.) instead of a live
  terminal. The lab start/stop calls are real and will create `lab_instances`
  rows.
- **AI chatbot** — the `/api/chatbot/message` endpoint is a placeholder that
  echoes your question. Plug an LLM into `app/services/ai_service.py` and the
  frontend picks it up automatically.
