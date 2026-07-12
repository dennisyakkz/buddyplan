# Installation

This guide expands on the [root README](../README.md) with deployment details for a typical self-hosted setup.

## Prerequisites

- Docker and Docker Compose (recommended), or Python 3.11+ for manual deployment
- A host with persistent storage for the SQLite database volume
- Android devices for the mobile and wall-display apps (optional but typical)

## Backend with Docker

### 1. Configure environment

```bash
cd backend
cp .env.example .env
```

Generate and set secrets in `.env`:

```bash
python -c "import secrets; print('SESSION_SECRET_KEY=' + secrets.token_hex(32))"
python -c "import secrets; print('TOKEN_PEPPER=' + secrets.token_hex(32))"
```

### 2. Start the service

```bash
docker compose up --build -d
```

The backend listens on port `8000`. Data is stored in the `buddyplan-data` Docker volume at `/data/buddyplan.db` inside the container.

For production on a NAS (OpenMediaVault) or any host without a git checkout, use a pre-built image from GHCR — see [Releases & GHCR](releases.md).

### 3. First-run setup

Open `http://<your-server>:8000`.

- If no admin user exists, you are redirected to `/setup` to create one.
- Alternatively, pre-create the admin by setting `BUDDYPLAN_ADMIN_USERNAME`, `BUDDYPLAN_ADMIN_PASSWORD`, and optionally `BUDDYPLAN_ADMIN_NAME` in `.env` before starting.

After setup, log in via the web UI to manage persons, tasks, and calendar events.

## Backend without Docker

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

For local development, add `BUDDYPLAN_DEV=1` to `.env` to allow optional ephemeral secrets. **Do not use this in production.**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Database migrations run automatically on startup.

## Android apps

Build release APKs on a development machine, then sideload or distribute through your own channel.

### Mobile app (Buddyplan)

```bash
cd mobile_app
flutter pub get
flutter build apk --release
```

Output: `build/app/outputs/flutter-apk/app-release.apk`  
Package ID: `nl.buddyplan.mobile`

### Wall display (Buddyplan Display)

```bash
cd dashboard_app
./gradlew assembleRelease
```

Output: `app/build/outputs/apk/release/app-release.apk`  
Package ID: `nl.buddyplan.display`

### Configure clients

1. Install each APK on the target device.
2. Open app settings and enter your server URL (e.g. `http://192.168.1.10:8000` or your HTTPS reverse-proxy URL).
3. Log in with a household member account created in the web admin.

There is no hardcoded default server URL in production builds.

## Upgrades and breaking changes

| Change | Effect |
|--------|--------|
| New `applicationId` (package rename) | Install as a **new app**; old local prefs/cache are not migrated |
| `TOKEN_PEPPER` rotation | All mobile/display API tokens become invalid; re-login required |
| `SESSION_SECRET_KEY` rotation | Web sessions expire; admins must log in again |
| Database path change | Plan export/import or volume migration |

## Reverse proxy (optional)

For HTTPS or external access, place Buddyplan behind nginx, Caddy, or Traefik. Proxy `/` to `http://127.0.0.1:8000` and terminate TLS at the proxy.

Ensure WebSocket and session cookies work if you add real-time features later; the current web UI uses standard HTTP sessions.

## Further reading

- [Releases & GHCR](releases.md) — publish images and deploy on OpenMediaVault
- [SECURITY.md](../SECURITY.md) — secrets, reporting vulnerabilities
- [Afvalwijzer](afvalwijzer.md) — optional NL waste-collection tasks
