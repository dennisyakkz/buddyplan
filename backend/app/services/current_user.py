from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.dashboard_service import PersonService
from app.services.token_utils import hash_api_token


def get_current_user(request: Request, db: Session = Depends(get_db)):
    service = PersonService(db)

    # Bearer token auth (used by the mobile app)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token_str = auth_header[7:].strip()
        from app.models import PersonApiToken
        token_hash = hash_api_token(token_str)
        token_record = (
            db.query(PersonApiToken)
            .filter(
                PersonApiToken.token_hash == token_hash,
                PersonApiToken.revoked_at.is_(None),
            )
            .first()
        )
        if token_record:
            token_record.last_used_at = datetime.now(timezone.utc)
            db.commit()
            user = service.get(token_record.person_id)
            if user:
                return user

    # Session-based auth (used by the web UI)
    person_id = request.session.get("person_id")
    user = service.get(int(person_id)) if person_id else None

    if not user:
        raise HTTPException(401, "Niet ingelogd")

    return user


def require_admin(user=Depends(get_current_user)):
    if not getattr(user, "is_admin", False):
        raise HTTPException(403, "Admin rechten vereist")
    return user
