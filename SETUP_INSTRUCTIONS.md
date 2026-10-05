# CyberArcade — Setup Instructions for Friends

## What you need installed first
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+

---

## Step 1 — Create your database
Open pgAdmin or psql and create a new database:
```sql
CREATE DATABASE cyberarcade;
```

---

## Step 2 — Configure the backend
Go into `Backend/Backend/cyberarcade-backend/` and create a `.env` file:
```
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/cyberarcade
SECRET_KEY=any-long-random-string-you-make-up
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

## Step 3 — Install backend dependencies and start it
```
cd Backend/Backend/cyberarcade-backend
python -m venv .venv
.\.venv\Scripts\activate        # Windows
# source .venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

---

## Step 4 — Import all courses
Open a second terminal in the same folder (with .venv active):
```
.\.venv\Scripts\python.exe import_course.py course_export.json
```
This loads all the courses, labs, and tasks into your database.

---

## Step 5 — Install frontend dependencies and start it
```
cd Frontend/Frontend/cyberarcade
npm install
npm run dev
```
Open http://localhost:5173 in your browser.

---

## Step 6 — Create your admin account
Register normally through the app, then in psql run:
```sql
UPDATE users SET role = 'system_admin' WHERE email = 'your@email.com';
```

---

## Notes
- Certificates are earned per-user — you earn your own by completing courses
- Each person needs their own `.env` with their own DB credentials
- The `.env` file is NOT included in the zip for security reasons
