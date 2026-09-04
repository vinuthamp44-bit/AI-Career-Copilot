# AI Career Copilot

A modular Flask + React career assistant for resume analysis, ATS matching, job fit, interview practice, and learning roadmaps.

## Requirements

- Python 3.10+
- Node.js 18+
- MySQL 8+ (optional for local demo; SQLite is the default fallback)

## Run locally

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The dashboard demo login accepts any values in this prototype; the API uses real JWT registration and login at `/api/auth/register` and `/api/auth/login`.

## MySQL setup

Run `database/schema.sql`, then set `DATABASE_URL` in `backend/.env` to `mysql+pymysql://user:password@localhost:3306/career_copilot`. Never put secrets in frontend code.

## API highlights

- `GET /api/health`
- `POST /api/auth/register`, `POST /api/auth/login`
- `GET /api/dashboard`
- `POST /api/resume/analyze` with multipart field `resume` (PDF, max 5 MB)
- `POST /api/ats/analyze`, `/api/jobs/match`, `/api/interview/questions`, `/api/interview/evaluate`

The NLP service is intentionally provider-agnostic. Replace or extend `backend/services/ai_service.py` with a Sentence Transformers or LLM adapter while keeping route contracts stable.
