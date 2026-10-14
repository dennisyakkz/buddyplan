# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Buddyplan (formerly "fiona"; the folder, APK names and some local files still use the old name) is a family planner with three parts:
- `backend/`: FastAPI + SQLAlchemy + SQLite + Alembic. It serves the Jinja2 web admin (cookie `buddyplan_session`) and the REST API under `/api` (Bearer tokens from `POST /api/auth/login`).
- `mobile_app/`: a Flutter app (Riverpod, Dio, Drift offline cache).
- `dashboard_app/`: a **native Kotlin Android** app for the wall tablet (Views/XML, Room, Retrofit). It is not Flutter.

Neither app has a compiled-in backend URL. The user enters it in each app's settings.

## Git
- The repo is on a root-owned mount, so plain `git` fails with "dubious ownership". Use `git -c safe.directory=/media/Data/projects/fiona-todo ...`.
- Work on feature branches and merge through PRs. Don't commit directly to `main`.
- Commit messages are one short imperative sentence ending in a period, e.g. `Fix agenda colors, times, edit flow, and false offline banner.`
- Never commit APKs (`*.apk` is gitignored).

## Backend
- Run it locally with `cd backend && docker compose up --build` (port 8000, reads `backend/.env`).
- The code does not load `.env`, so a bare `uvicorn` run needs the env vars exported or `BUDDYPLAN_DEV=1`.
- `SESSION_SECRET_KEY` and `TOKEN_PEPPER` are required unless `BUDDYPLAN_DEV=1`. Rotating `TOKEN_PEPPER` logs out every device.
- Alembic migrations run automatically at startup (`app/services/migrate.py`), and `seed_database` runs on every start.
- Migrations are hand-numbered (`00N_name.py`, with `revision` equal to the file stem) and must use `op.batch_alter_table` because the database is SQLite. Use `/new-migration`.
- `001_initial_schema` runs `Base.metadata.create_all` from the *current* models, so a fresh database already contains later columns. Later migrations must check that a column or table exists before adding it (see `003_person_profile_color.py`).
- Tailwind CSS is prebuilt. After changing templates, JS class names or `tailwind.config.js`, run `npm run build:css` in `backend/` and commit `app/static/css/tailwind.css`. The Docker image has no Node step.
- Lint and format with `ruff` (configured in `backend/ruff.toml`). CI (`.github/workflows/backend-tests.yml`, Python 3.11) fails PRs on `ruff check`, `ruff format --check` or `pytest`.
- Tests: `pip install -r requirements-dev.txt`, then `pytest` in `backend/` (single test: `pytest tests/test_tasks.py::test_task_lifecycle`). `tests/conftest.py` points the app at a temporary SQLite DB *before* importing `app`, because `app.main` migrates and seeds at import time. Use the `make_user` fixture for users; `persons.name` is unique.

## Mobile app
- `flutter analyze` and `flutter test` (there is only a smoke test).
- After changing Drift tables, run `dart run build_runner build --delete-conflicting-outputs` and commit `lib/data/local_database.g.dart`.

## Dashboard app
- `./gradlew assembleRelease` needs JDK 17+ and the Android SDK. There are no tests.

## Cross-cutting
- All user-facing text is **Dutch**, hardcoded with no l10n files. This includes backend error messages. Keep new strings in Dutch.
- The brand palette lives in `brand/brandbook.md` and is mirrored in `backend/tailwind.config.js`, `mobile_app/lib/ui/buddyplan_colors.dart` and `dashboard_app/app/src/main/res/values{,-night}/colors.xml`. Keep all of them in sync.
- The material-icons JSON is duplicated in `backend/app/static/data/` and `mobile_app/assets/data/`. Update both copies.
- API changes affect both apps. Check the mobile (`/api/mobile/*`, `/api/tasks`, `/api/agenda`) and dashboard (`/api/dashboard*`) clients.

## Release
- Publishing a GitHub Release tagged `vX.Y.Z` triggers `.github/workflows/publish-backend.yml`, which pushes `ghcr.io/dennisyakkz/buddyplan-backend:X.Y.Z`.
- Production runs `backend/docker-compose.prod.yml` on OpenMediaVault. Use `/release`.
