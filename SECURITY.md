# Security Policy

## Supported versions

Buddyplan is self-hosted software. Security fixes are applied on the default branch; there is no separate long-term support matrix. Run a recent checkout or release when deploying to production.

## Reporting a vulnerability

If you discover a security issue, please **do not** open a public GitHub issue with exploit details.

Report it privately to the repository maintainer (see [buddyplan.nl](https://buddyplan.nl) for contact). Include:

- A clear description of the issue
- Steps to reproduce
- Impact assessment (data exposure, authentication bypass, etc.)
- Your environment (Buddyplan version/commit, deployment method)

We aim to acknowledge reports within a reasonable timeframe and coordinate a fix before public disclosure when appropriate.

## Deployment requirements

### Required secrets (production)

Never run a production instance without setting these in `.env` (or your orchestrator's secret store):

| Variable | Purpose |
|----------|---------|
| `SESSION_SECRET_KEY` | Signs web admin session cookies |
| `TOKEN_PEPPER` | HMAC key for hashing mobile/display API tokens at rest |

Generate strong random values:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Do **not** use example placeholders, short passwords, or committed `.env` files.

`BUDDYPLAN_DEV=1` relaxes secret requirements for **local development only**. Do not enable it in production.

### First-run admin account

- On first start, create the admin via `/setup` or set `BUDDYPLAN_ADMIN_USERNAME` / `BUDDYPLAN_ADMIN_PASSWORD` in `.env`.
- There is **no** default admin password in the source code.
- Use a strong, unique password for the admin account.

### What not to commit

- `.env` files with real secrets
- Production SQLite databases (`*.db`)
- Google OAuth client secrets or refresh tokens (configure via the admin UI; stored in your database)
- Built APK files, keystores, or local virtual environments

See the root [`.gitignore`](.gitignore).

## Token and session handling

- Web sessions use the `buddyplan_session` cookie, signed with `SESSION_SECRET_KEY`.
- Mobile and display apps use bearer tokens; only HMAC hashes are stored server-side (`TOKEN_PEPPER`).
- Rotating `TOKEN_PEPPER` invalidates existing API tokens — users must log in again on devices.
- Rotating `SESSION_SECRET_KEY` invalidates active web sessions.

## Network exposure

Buddyplan is intended for **private or trusted household networks** (LAN, VPN, or reverse proxy with TLS).

- Bind to localhost or place the service behind a reverse proxy with HTTPS when exposed beyond your home network.
- Restrict firewall access to the backend port (default `8000`).
- The backend has no built-in rate limiting; consider a reverse proxy for internet-facing deployments.

## Third-party integrations

- **Afvalwijzer** (optional, Netherlands): fetches public schedule data from [mijnafvalwijzer.nl](https://www.mijnafvalwijzer.nl) using postcode and house number you configure. No API key is stored for this service.
- **Google Calendar** (optional): OAuth credentials are entered in the admin UI and stored in your local database. Treat them as secrets and restrict admin access.

## Updates

- Pull or rebuild the backend image regularly for security patches in dependencies.
- After upgrading, verify migrations complete successfully and rotate secrets if you suspect compromise.
- Reinstall mobile/display APKs when package IDs or signing keys change; local app data from old package IDs is not migrated automatically.

## Responsible disclosure

We appreciate coordinated disclosure. Please allow time to investigate and release a fix before sharing details publicly.
