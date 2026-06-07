"""
Authentication primitives.

We use the `bcrypt` library directly (not `passlib`) to avoid the
`passlib.handlers.bcrypt._load_backend_mixin` compatibility bug that
appears with newer bcrypt releases.
"""
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from app.config import get_settings


# bcrypt has a hard 72-byte input limit. Truncate silently to avoid
# ValueError on long passwords.
_BCRYPT_MAX = 72


def _truncate(plain: str) -> bytes:
    return plain.encode("utf-8")[:_BCRYPT_MAX]


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with a fresh salt."""
    return bcrypt.hashpw(_truncate(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if `plain` matches the bcrypt-hashed `hashed`."""
    try:
        return bcrypt.checkpw(_truncate(plain), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(user_uuid: str, role: str) -> str:
    settings = get_settings()
    payload = {
        "sub": user_uuid,
        "role": role,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> Optional[dict]:
    try:
        settings = get_settings()
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except JWTError:
        return None
