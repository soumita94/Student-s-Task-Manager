# Student Task Manager Deployment

This project has 2 deployable services:
- FastAPI backend (`app/main.py`)
- Streamlit frontend (`app/frontend.py`)

## Important free-tier reality

- Railway and Render free tiers can change over time (credits, sleep, bandwidth limits).
- For truly "no card, always free", use free resources where available and expect sleeping services.
- Use a free Postgres provider (for example Neon/Supabase free tier) instead of SQLite in production.

## 1) Deploy on Render (recommended path here)

This repo includes `render.yaml` for Blueprint deploy.

### Steps
1. Push this repo to GitHub.
2. In Render, choose **New +** -> **Blueprint** -> select your repo.
3. Render creates:
   - `student-task-api`
   - `student-task-frontend`
4. Set environment variables:
   - On API service:
     - `GOOGLE_API_KEY` = your Gemini key
     - `DATABASE_URL` = your Postgres async URL
     - `LLM_PROVIDER=gemini`
     - `GEMINI_MODEL=gemini-2.5-flash`
   - On frontend service:
     - `STM_API_BASE` = URL of `student-task-api` (for example `https://student-task-api.onrender.com`)
5. Deploy both services.
6. Verify:
   - API health: `https://<api-service>/health`
   - Frontend UI: `https://<frontend-service>`

## 2) Deploy on Railway

Create 2 Railway services from the same repo.

### Backend service
- Start command:
  - `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Variables:
  - `GOOGLE_API_KEY`
  - `LLM_PROVIDER=gemini`
  - `GEMINI_MODEL=gemini-2.5-flash`
  - `DATABASE_URL` (Railway Postgres URL or external free Postgres)

### Frontend service
- Start command:
  - `streamlit run app/frontend.py --server.port $PORT --server.address 0.0.0.0`
- Variables:
  - `STM_API_BASE=https://<your-backend-service-domain>`

## Local env example

Use `.env` for local runs:

```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_key
GEMINI_MODEL=gemini-2.5-flash
DATABASE_URL=sqlite+aiosqlite:///./student_tasks.db
```

## Notes

- Gemini may return `503` during high demand; retry is already implemented.
- If Gemini quota is exhausted, switch provider variables to OpenAI.
