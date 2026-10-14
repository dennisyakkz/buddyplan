---
name: release
description: Cut a Buddyplan release (version bump PR, vX.Y.Z tag, GitHub Release that publishes the backend image to GHCR).
disable-model-invocation: true
---

Release version: $ARGUMENTS (format `X.Y.Z`; ask if missing)

Use `git -c safe.directory=/media/Data/projects/fiona-todo` for every git command.

1. Confirm the working tree is clean and `main` is up to date with `origin`.
2. Create branch `release/vX.Y.Z` and bump the versions:
   - `mobile_app/pubspec.yaml`: set `version:` to `X.Y.Z+<build>`, incrementing the build number.
   - `dashboard_app/app/build.gradle*`: set `versionName = "X.Y.Z"` and increment `versionCode`. The in-app self-upgrade relies on `versionCode` increasing.
   - `backend/docker-compose.prod.yml` and `README.md`: update the example and default `BUDDYPLAN_VERSION`.
3. If templates or Tailwind classes changed since the last tag, rebuild `backend/app/static/css/tailwind.css` (`npm run build:css`) and include it.
4. Commit with the message `Release vX.Y.Z: <short summary>.` (imperative, ending in a period), push, and open a PR with `gh pr create`. Stop and let the user merge it.
5. After the merge, create the release from `main` with `gh release create vX.Y.Z --generate-notes`. This triggers `publish-backend.yml`, which builds `ghcr.io/dennisyakkz/buddyplan-backend:X.Y.Z` and `:latest`.
6. Watch the workflow with `gh run watch`. Then tell the user to set `BUDDYPLAN_VERSION=X.Y.Z` on the OpenMediaVault host and run `docker compose -f docker-compose.prod.yml pull && up -d`.
7. Optionally build the APKs (`flutter build apk --release` and `./gradlew assembleRelease`). Never commit them. The dashboard APK can be uploaded through the admin UI for self-upgrade.
