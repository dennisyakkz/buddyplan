---
name: release
description: Cut a Buddyplan release. Syncs every version number (mobile, dashboard, backend compose, docs) to the new vX.Y.Z, opens the release PR, and after the merge publishes the GitHub Release that builds the backend image on GHCR. Use whenever the user asks for a release or a new version.
argument-hint: "[X.Y.Z]"
---

Release version: $ARGUMENTS

When the user asks for a release, do all of this without asking for each step. Only stop where it says so.

## 1. Pick the version
- Latest release: `git fetch --tags origin && git tag --list 'v*' --sort=-v:refname | head -1`.
- If no version was given, propose the next patch version (and say what minor/major would be). Ask with one question and continue with the answer.
- The version must be `X.Y.Z`, higher than the latest tag, with MINOR and PATCH below 100.

## 2. Prepare the release branch
1. The working tree must be clean. If it isn't, stop and ask.
2. `git switch -c release/vX.Y.Z origin/main`.
3. `python3 scripts/bump_version.py X.Y.Z`, then `python3 scripts/bump_version.py --check X.Y.Z`. This sets:
   - `mobile_app/pubspec.yaml`: `version: X.Y.Z+<code>`
   - `dashboard_app/app/build.gradle.kts`: `versionName = "X.Y.Z"`, `versionCode = <code>`
   - `backend/docker-compose.prod.yml`, `README.md`, `docs/releases.md`: `BUDDYPLAN_VERSION` default and examples

   `<code>` = MAJOR*10000 + MINOR*100 + PATCH, so it always increases (Android refuses to install a lower versionCode). If you find another file that carries the version, add it to the script instead of editing it by hand.
4. If anything under `backend/app/templates`, `backend/app/static/js` or `backend/tailwind.config.js` changed since the last tag (`git diff --stat vPREV origin/main -- <paths>`), run `npm run build:css` in `backend/` and include `app/static/css/tailwind.css`.
5. Run the backend checks in `backend/`: `ruff check .`, `ruff format --check .` and `pytest` (with `.venv/bin/` if no venv is active). If any fail, stop and report.

## 3. Open the PR
1. Commit: `Release vX.Y.Z: <short summary of what changed since vPREV>.` (one imperative sentence ending in a period, plus the Co-Authored-By trailer).
2. `git push -u origin release/vX.Y.Z`.
3. `gh pr create --base main --title "Release vX.Y.Z" --body ...`. In the body, list the merged PRs and notable commits since `vPREV` (`git log --oneline vPREV..origin/main`) and the synced version numbers.
4. `gh pr checks --watch` and report the result with the PR link.
5. **Stop.** The user merges the PR (or explicitly asks you to merge with `gh pr merge --merge`).

## 4. Publish (after the merge)
1. `git fetch origin && git switch main && git pull --ff-only`, then `python3 scripts/bump_version.py --check X.Y.Z` on `main`. Don't publish if it fails.
2. `gh release create vX.Y.Z --target main --title "vX.Y.Z" --generate-notes`. Always use exactly `vX.Y.Z` as the tag and the title.
3. `gh run watch` on the `publish-backend.yml` run it triggers. It pushes `ghcr.io/dennisyakkz/buddyplan-backend:X.Y.Z` and `:latest`.
4. Tell the user to set `BUDDYPLAN_VERSION=X.Y.Z` on the OpenMediaVault host and run `docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d`.
5. If Flutter or the Android SDK is available, offer to build the APKs (`flutter build apk --release`, `./gradlew assembleRelease`). Never commit them. The dashboard APK is uploaded through the web admin for self-upgrade.
