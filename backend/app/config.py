import logging
import os
import secrets

logger = logging.getLogger(__name__)

APP_NAME = "Buddyplan"
APP_NAME_DISPLAY = "Buddyplan"
APP_NAME_TABLET = "Buddyplan Display"

_DEV_TOKEN_PEPPER = "dev-only-do-not-use-in-production"


def is_dev_mode() -> bool:
    return os.environ.get("BUDDYPLAN_DEV", "").strip().lower() in ("1", "true", "yes")


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value and not is_dev_mode():
        raise RuntimeError(f"{name} is required (set in .env or environment)")
    return value


def env_secret(name: str, *, dev_fallback: str | None = None) -> str:
    value = os.environ.get(name, "").strip()
    if value:
        return value
    if is_dev_mode():
        if dev_fallback is not None:
            logger.warning(
                "%s not set; using dev-only fallback (local development only)",
                name,
            )
            return dev_fallback
        logger.warning(
            "%s not set; using ephemeral dev secret (sessions reset on restart)",
            name,
        )
        return secrets.token_hex(32)
    raise RuntimeError(f"{name} is required (set in .env or environment)")


def get_token_pepper() -> str:
    return env_secret("TOKEN_PEPPER", dev_fallback=_DEV_TOKEN_PEPPER)
