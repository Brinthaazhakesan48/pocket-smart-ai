# PocketSmart AI

A complete FastAPI + Jinja2 + SQLite + Gemini application based on the supplied PocketSmart AI project documentation.

## What is included
- Home Interior Budget Planner
- Party Budget Planner
- Jewelry Budget Planner with optional outfit image
- Gemini multimodal integration through the current `google-genai` SDK
- Structured JSON AI output validated by Pydantic
- JWT authentication plus secure HTTP-only session cookie
- Registration, login, logout, session info/data
- Recommendation history and detail API
- Responsive HTML/CSS/JavaScript UI
- Deterministic fallback recommendations when Gemini is not configured or fails
- Search links for Amazon, Flipkart, IKEA, Swiggy, Zomato, and OYO instead of pretending to have live marketplace inventory
- Pytest smoke tests
- Dockerfile and docker-compose configuration

## Architecture
`app/main.py` -> routers -> services -> Gemini/catalog/fallback -> SQLite.

The supplied document contains both Flask and FastAPI references. This implementation follows the later FastAPI milestones and keeps the route names requested in the document.

## VS Code setup
1. Install Python 3.12+ and VS Code.
2. Extract this project and open the folder in VS Code.
3. Open **Terminal > New Terminal**.
4. Create a virtual environment:
   - Windows: `py -3.12 -m venv .venv`
   - macOS/Linux: `python3 -m venv .venv`
5. Activate it:
   - Windows PowerShell: `.venv\\Scripts\\Activate.ps1`
   - Windows CMD: `.venv\\Scripts\\activate.bat`
   - macOS/Linux: `source .venv/bin/activate`
6. Install dependencies: `pip install -r requirements.txt`
7. Copy `.env.example` to `.env`.
8. For AI mode, put your Gemini API key in `GEMINI_API_KEY`.
9. Start the server: `uvicorn app.main:app --reload`
10. Open `http://127.0.0.1:8000`.

## AI configuration
The documentation names Gemini 1.5 Flash Pro, but that model is no longer the appropriate current default. The project uses `GEMINI_MODEL=gemini-3.8-flash` by default. You can change it in `.env` if your account has access to another supported model.

If `GEMINI_API_KEY` is blank or `AI_ENABLED=false`, the application still works using deterministic fallback recommendations. This makes UI/API testing possible without an API key.

## Test
With the virtual environment active:
`pytest -q`

API health check:
`GET http://127.0.0.1:8000/health`

Interactive API docs:
`http://127.0.0.1:8000/docs`

## Docker
Create `.env`, then:
`docker compose up --build`

Open `http://127.0.0.1:8000`.

## Production notes
- Replace the development secret with a long random secret.
- Use HTTPS so the authentication cookie is protected in transit.
- Move SQLite to PostgreSQL for multi-user production workloads.
- Replace catalog search links with licensed marketplace/vendor APIs if live price/availability data is required.
- Add CSRF protection if cookie-authenticated state-changing requests are exposed to untrusted origins.
- Add rate limiting, structured logging, monitoring, backups, and email verification before public deployment.
