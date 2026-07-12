# Buddyplan backend

FastAPI backend with web admin UI, REST API, SQLite database, and Docker deployment.

See the [root README](../README.md) for full setup instructions.

## Docker

```bash
cp .env.example .env
# Fill SESSION_SECRET_KEY and TOKEN_PEPPER in .env
docker compose up --build
```

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add BUDDYPLAN_DEV=1 to .env for optional secrets during development
uvicorn app.main:app --reload --port 8000
```

Database migrations run automatically on startup (Alembic).

## Web CSS (Tailwind)

The web UI uses a compiled Tailwind bundle (`app/static/css/tailwind.css`). After changing `input.css`, `tailwind.config.js`, or Tailwind classes in templates/JS, rebuild and commit the output:

```bash
cd backend
npm install
npm run build:css
```

Docker images copy only `app/` (no Node), so `tailwind.css` must be committed.
