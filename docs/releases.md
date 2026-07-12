# Releases and GHCR

Buddyplan backend images are published to [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry) (GHCR) when **you** create a GitHub Release. Nothing is pushed on every commit.

Image name pattern:

```text
ghcr.io/<github-owner>/buddyplan-backend:<version>
```

Example: `ghcr.io/acme/buddyplan-backend:1.0.0`

## One-time setup

### 1. Create the GitHub repository

1. On GitHub: **New repository** (e.g. `buddyplan`).
2. Do **not** initialize with a README if you already have a local checkout.
3. Push your local project:

```bash
cd /path/to/buddyplan
git remote add origin git@github.com:YOUR_GITHUB_USER/buddyplan.git
git branch -M main
git push -u origin main
```

### 2. Enable the workflow

The workflow file [`.github/workflows/publish-backend.yml`](../.github/workflows/publish-backend.yml) is included in the repo. After the first push to `main`, it appears under **Actions**.

No extra secrets are required: `GITHUB_TOKEN` is provided automatically and can push to GHCR for packages linked to this repository.

### 3. Make the package public (after first publish)

The first image push creates the package under your GitHub account or org:

1. GitHub → your profile or org → **Packages**
2. Open **buddyplan-backend**
3. **Package settings** → **Change visibility** → **Public**

Public images can be pulled on OpenMediaVault and other hosts **without** registry login.

## Publish a release (you decide when)

1. Ensure `main` contains the code you want to ship.
2. GitHub → **Releases** → **Draft a new release**
3. Choose a tag, e.g. `v1.0.0` (create new tag on `main`)
4. Title and release notes (optional)
5. Click **Publish release**

The **Publish backend image** workflow runs automatically and pushes:

- `ghcr.io/<owner>/buddyplan-backend:1.0.0` (tag without `v` prefix)
- `ghcr.io/<owner>/buddyplan-backend:latest`

Check progress under **Actions**. When green, the image is ready to pull.

### Manual publish (without a GitHub Release)

**Actions** → **Publish backend image** → **Run workflow** → enter a tag (e.g. `1.0.0-rc1`). This pushes only that tag, not `latest`.

## Deploy on OpenMediaVault (or any Docker host)

On the NAS or server:

```bash
mkdir -p ~/buddyplan && cd ~/buddyplan
curl -O https://raw.githubusercontent.com/YOUR_GITHUB_USER/buddyplan/main/backend/docker-compose.prod.yml
curl -O https://raw.githubusercontent.com/YOUR_GITHUB_USER/buddyplan/main/backend/.env.example
cp .env.example .env
# Edit .env: SESSION_SECRET_KEY, TOKEN_PEPPER, etc.
```

Set image coordinates in `.env` or export before `compose up`:

```bash
export GHCR_OWNER=YOUR_GITHUB_USER
export BUDDYPLAN_VERSION=1.0.0
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

In OMV’s Compose UI: paste `docker-compose.prod.yml`, set environment variables `GHCR_OWNER` and `BUDDYPLAN_VERSION`, mount or paste `.env`, then deploy.

## Upgrade

1. Publish a new GitHub Release (e.g. `v1.0.1`).
2. On the server: set `BUDDYPLAN_VERSION=1.0.1`, then `docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d`.

The `buddyplan-data` volume keeps your SQLite database across upgrades.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `pull access denied` | Package still private → set visibility to Public, or `docker login ghcr.io` |
| Workflow did not run | Release must be **published**, not draft; or run workflow manually |
| Wrong image name | Image owner is the GitHub **user/org**, lowercase (e.g. `ghcr.io/dennis/buddyplan-backend`) |
