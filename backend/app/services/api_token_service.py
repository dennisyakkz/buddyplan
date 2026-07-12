from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import PersonApiToken
from app.services.token_utils import generate_api_token, hash_api_token

VALID_DEVICE_TYPES = frozenset({"mobile", "dashboard"})


def _normalize_device_type(device_type: str | None) -> str:
    if device_type and device_type.strip().lower() in VALID_DEVICE_TYPES:
        return device_type.strip().lower()
    return "mobile"


def issue_token_for_device(
    db: Session,
    *,
    person_id: int,
    device_id: str,
    device_name: str | None = None,
    device_type: str | None = None,
) -> str:
    device_id = device_id.strip()
    if not device_id:
        raise ValueError("device_id is required")

    plain_token = generate_api_token()
    token_hash = hash_api_token(plain_token)
    now = datetime.now(timezone.utc)
    normalized_type = _normalize_device_type(device_type)
    display_name = (device_name or "").strip() or "Onbekend apparaat"

    record = (
        db.query(PersonApiToken)
        .filter(
            PersonApiToken.person_id == person_id,
            PersonApiToken.device_id == device_id,
        )
        .first()
    )
    if record:
        record.token_hash = token_hash
        record.device_name = display_name
        record.device_type = normalized_type
        record.revoked_at = None
        record.last_used_at = now
    else:
        record = PersonApiToken(
            person_id=person_id,
            device_id=device_id,
            device_name=display_name,
            device_type=normalized_type,
            token_hash=token_hash,
            last_used_at=now,
        )
        db.add(record)

    db.commit()
    return plain_token


def list_active_devices(db: Session, person_id: int) -> list[PersonApiToken]:
    return (
        db.query(PersonApiToken)
        .filter(
            PersonApiToken.person_id == person_id,
            PersonApiToken.revoked_at.is_(None),
        )
        .order_by(
            PersonApiToken.last_used_at.desc().nullslast(),
            PersonApiToken.created_at.desc(),
        )
        .all()
    )


def revoke_device(db: Session, *, person_id: int, device_id: str) -> bool:
    record = (
        db.query(PersonApiToken)
        .filter(
            PersonApiToken.person_id == person_id,
            PersonApiToken.device_id == device_id,
            PersonApiToken.revoked_at.is_(None),
        )
        .first()
    )
    if not record:
        return False
    record.revoked_at = datetime.now(timezone.utc)
    db.commit()
    return True


def device_to_dict(
    record: PersonApiToken,
    *,
    current_token_hash: str | None = None,
) -> dict:
    return {
        "id": record.id,
        "device_id": record.device_id,
        "device_name": record.device_name or "Onbekend apparaat",
        "device_type": record.device_type or "mobile",
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "last_used_at": record.last_used_at.isoformat() if record.last_used_at else None,
        "is_current": bool(
            current_token_hash and record.token_hash == current_token_hash
        ),
    }
