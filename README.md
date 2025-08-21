# interview-saas

Real-time AI Interview Practice SaaS — Fullstack example built with:
- Frontend: Next.js + Clerk + Tailwind
- Backend: FastAPI (Python 3.11+) + WebSockets
- DB: Supabase (Postgres + Storage)
- LLM: Google Gemini via google-genai SDK
- Resume parsing: PyMuPDF (+ Tesseract OCR fallback)

This repo is configured for local development using **venv** (no Docker required).

---

## Quick overview
- Frontend: `frontend/`
- Backend: `backend/`
- Supabase schema: `supabase/schema.sql`
- Env sample: `.env.example`

---

## Quick start (local, venv)

1. Clone:
   ```bash
   git clone <this-repo>
   cd interview-saas

2. Create & activate venv:


python3.11 -m venv .venv
source .venv/bin/activate   # mac / linux
.venv\Scripts\activate 

3. Backend dependencies:

cd backend
pip install -r requirements.txt

4. Frontend dependencies:

cd ../frontend
npm install

5. Create .env files from .env.example (both backend and frontend). Fill in keys:

CLERK_PUBLISHABLE_KEY, CLERK_SECRET_KEY, CLERK_JWT_KEY (Clerk)

SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY

GEMINI_API_KEY (or Google GenAI project config)

BACKEND_URL (e.g. http://localhost:8000)

6. Start backend:

cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

7. Start frontend:

cd ../frontend
npm run dev
# open http://localhost:3000

