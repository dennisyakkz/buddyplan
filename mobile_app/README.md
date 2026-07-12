# Buddyplan mobile app

Flutter client for Buddyplan (todo list and agenda on phone/tablet).

See the [root README](../README.md) for project overview, backend setup, and environment variables.

## Build

```bash
flutter pub get
flutter run              # debug
flutter build apk --release
```

Configure the backend URL in the app settings after install. In debug builds, an empty server URL falls back to `http://localhost:8000`.
