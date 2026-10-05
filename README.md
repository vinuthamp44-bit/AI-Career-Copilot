# AI Career Copilot

A modular Flask + React placement assistant for resume analysis, ATS matching, placement readiness, application tracking, GD and interview practice, and actionable learning plans.

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

Open `http://localhost:5173`. The application uses real JWT registration, login, and onboarding at `/api/auth/register`, `/api/auth/login`, and `/api/profile`.

## MySQL setup

Run `database/schema.sql`, then set `DATABASE_URL` in `backend/.env` to `mysql+pymysql://user:password@localhost:3306/career_copilot`. Never put secrets in frontend code.

For Google sign-in, create a Google OAuth Web client and set the same client ID in `backend/.env` as `GOOGLE_CLIENT_ID` and `frontend/.env` as `VITE_GOOGLE_CLIENT_ID`. Add `http://127.0.0.1:5173` and `http://localhost:5173` as authorized JavaScript origins, then restart both servers.

Google sign-in uses Google Identity Services. The browser receives an ID token using the public client ID, and Flask verifies that token server-side before issuing the application's JWT. No Google client secret is required in the frontend.

## API highlights

- `GET /api/health`
- `POST /api/auth/register`, `POST /api/auth/login`
- `GET /api/dashboard`
- `POST /api/profile`
- `POST /api/resume/analyze` with multipart field `resume` (PDF, max 5 MB)
- `POST /api/ats/analyze`, `/api/jobs/match`, `/api/interview/questions`, `/api/interview/evaluate`
- `GET /api/career-readiness` for the evidence-based placement score and next actions
- `/api/applications` for authenticated job application CRUD and status filtering
- `POST /api/gd/evaluate`, `POST /api/resume/improve-bullet`, and `POST /api/jobs/analyze-description`
- `GET /api/skill-gaps` and `PATCH /api/skill-gaps/tasks/<id>` for saved seven-day skill plans

The analysis service is intentionally provider-agnostic and currently uses local keyword and response-structure heuristics; it does not call an external LLM. Replace or extend `backend/services/ai_service.py` with a Sentence Transformers or LLM adapter while keeping route contracts stable.
