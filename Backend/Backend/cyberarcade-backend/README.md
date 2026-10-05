# CyberArcade Backend — FastAPI

## Project Structure

```
cyberarcade-backend/
├── app/
│   ├── main.py                  ← FastAPI entry point
│   ├── core/
│   │   ├── config.py            ← Settings from .env
│   │   ├── database.py          ← Async SQLAlchemy engine
│   │   └── security.py          ← JWT + password hashing + RBAC
│   ├── models/                  ← SQLAlchemy ORM models
│   ├── schemas/                 ← Pydantic request/response models
│   ├── routers/
│   │   ├── auth.py              ← Register / Login / Refresh / Me
│   │   ├── courses.py           ← CRUD courses + modules
│   │   ├── labs.py              ← Labs, tasks, hints, auto-solve
│   │   ├── classes.py           ← Create/join classes, progress
│   │   ├── admin.py             ← Dashboard, user mgmt, audit
│   │   └── chatbot.py           ← AI chatbot messaging
│   └── services/
│       └── ai_service.py        ← LLM integration point
├── requirements.txt
├── .env                         ← Your local config (DO NOT commit)
├── .env.example                 ← Template
└── README.md
```

## Setup on Windows (VS Code)

### 1. Prerequisites

- **Python 3.11+** — [python.org](https://www.python.org/downloads/) (check "Add Python to PATH" during install)
- **PostgreSQL + pgAdmin** — already installed
- **VS Code** with the Python extension

### 2. Make Sure the Database Exists

In **pgAdmin**, confirm the `cyberarcade` database exists and has all 13 tables (from the schema file you ran earlier). If not, run `cyberarcade_schema.sql` in the Query Tool first.

### 3. Open Project in VS Code

```
File → Open Folder → cyberarcade-backend
```

### 4. Create Virtual Environment

In the **VS Code terminal** (`Ctrl + ~`):

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**If you get a script execution error** on `venv\Scripts\activate`, run this once as admin in PowerShell:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### 5. Configure `.env`

Open the `.env` file in VS Code and update with **your actual PostgreSQL password**:

```
DATABASE_URL=postgresql+asyncpg://cyberarcade_admin:YOUR_REAL_PASSWORD@localhost:5432/cyberarcade
SECRET_KEY=any-random-long-string-for-jwt-signing
```

To generate a strong SECRET_KEY, run in Python:
```python
import secrets; print(secrets.token_hex(32))
```

### 6. Run the Server

```powershell
uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 7. Test It

Open your browser:
- **Swagger UI (interactive):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health check:** http://localhost:8000/

## Quick Test Flow

Go to `http://localhost:8000/docs` and try:

1. **Register** — `POST /api/auth/register`
   ```json
   {
     "full_name": "Test User",
     "email": "test@example.com",
     "password": "password123"
   }
   ```

2. **Login** — `POST /api/auth/login`
   ```json
   {
     "email": "test@example.com",
     "password": "password123"
   }
   ```
   Copy the `access_token` from the response.

3. **Authorize** — Click the 🔒 **Authorize** button at the top of Swagger UI and paste the token.

4. **Get Profile** — `GET /api/auth/me` should now return your user data.

## Making Your First Admin User

After registering, your user has the `student` role. To make yourself an admin, run this in **pgAdmin Query Tool**:

```sql
UPDATE users SET role = 'system_admin' WHERE email = 'your_email@example.com';
```

Then log in again to get a new JWT with the admin role.

## API Endpoints Summary

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Login → returns JWT |
| POST | `/api/auth/refresh` | Refresh tokens |
| GET | `/api/auth/me` | Current user profile |

### Courses
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/courses` | List published courses |
| GET | `/api/courses/{id}` | Course detail + modules |
| GET | `/api/courses/{id}/labs` | List published labs in a course |
| POST | `/api/courses` | Create course (admin) |
| PUT | `/api/courses/{id}` | Update course (admin) |
| DELETE | `/api/courses/{id}` | Delete course (admin) |
| POST | `/api/courses/{id}/modules` | Add module (admin) |

### Labs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/labs/{id}` | Lab detail + tasks |
| POST | `/api/labs/{id}/start` | Start lab instance |
| POST | `/api/labs/{id}/stop` | Stop lab instance |
| GET | `/api/labs/{id}/status` | Instance status |
| POST | `/api/labs/tasks/{id}/submit` | Submit answer |
| GET | `/api/labs/tasks/{id}/hint` | Request hint (time-gated) |
| POST | `/api/labs/tasks/{id}/auto-solve` | Trigger auto-solve |

### Classes
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/classes` | Create class (instructor) |
| GET | `/api/classes/my-classes` | Instructor's classes |
| GET | `/api/classes/{id}/progress` | Student progress report |
| POST | `/api/classes/join` | Join class by code |
| GET | `/api/classes/enrolled` | Student's classes |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/stats` | Platform statistics |
| GET | `/api/admin/users` | List users |
| PUT | `/api/admin/users/{id}/role` | Change role |
| PUT | `/api/admin/users/{id}/status` | Activate/deactivate |
| GET | `/api/admin/audit-log` | Audit trail |

### Chatbot
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chatbot/message` | Send message to AI |
| GET | `/api/chatbot/history` | Conversation history |

## Next Steps (TODO)

1. **Docker Orchestrator** — Build the service that provisions attacker/victim containers (the `start_lab` endpoint has TODO comments where this goes)
2. **Guacamole Integration** — Connect lab instances to Apache Guacamole connections
3. **AI Chatbot** — Replace the placeholder in `app/services/ai_service.py` with your LLM API (OpenAI/Anthropic/etc.)
4. **Frontend** — Already wired in `../../../Frontend/Frontend/cyberarcade`. See that folder's README.

## Troubleshooting

**"Could not connect to database"** → Check that PostgreSQL is running, and that your password in `.env` matches the one you set in pgAdmin.

**"Module not found"** → Make sure your virtual environment is activated (you should see `(venv)` at the start of your terminal prompt).

**"Address already in use"** → Port 8000 is taken. Run on a different port: `uvicorn app.main:app --reload --port 8001`

**Password error during pip install** → Upgrade pip first: `python -m pip install --upgrade pip`
