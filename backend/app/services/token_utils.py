import hashlib
import hmac
import secrets

from app.config import get_token_pepper


def generate_api_token() -> str:
    return secrets.token_hex(32)


def hash_api_token(plain_token: str) -> str:
    pepper = get_token_pepper()
    return hmac.new(
        pepper.encode("utf-8"),
        plain_token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_api_token(plain_token: str, stored_hash: str) -> bool:
    if not plain_token or not stored_hash:
        return False
    computed = hash_api_token(plain_token)
    return hmac.compare_digest(computed, stored_hash)
