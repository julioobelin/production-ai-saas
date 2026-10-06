"""Password hashing and access tokens.

The placeholder secrets below are public examples. Production startup rejects them.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from app.core.exceptions import InvalidTokenError

_HASHER = PasswordHash.recommended()
_DUMMY_PASSWORD_HASH = _HASHER.hash("not-a-real-password")
_ALGORITHM = "HS256"

# Public placeholders. None of these are credentials for a real environment.
INSECURE_JWT_SECRETS = frozenset(
    {
        "replace-with-a-random-string-of-at-least-32-characters",
        "change-me",
        "changeme",
        "secret",
        "password",
        "test-jwt-secret-not-used-in-production-32",
    }
)


def hash_password(password: str) -> str:
    return _HASHER.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bool(_HASHER.verify(password, password_hash))
    except Exception:
        return False


def verify_password_or_dummy(password: str, password_hash: str | None) -> bool:
    """Run Argon2 even when the user does not exist, so login timing stays similar."""

    return verify_password(password, password_hash or _DUMMY_PASSWORD_HASH)


@dataclass(frozen=True)
class AccessToken:
    user_id: UUID
    organization_id: UUID


def create_access_token(
    *,
    user_id: UUID,
    organization_id: UUID,
    secret: str,
    expires_minutes: int,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "org": str(organization_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=_ALGORITHM)


def decode_access_token(token: str, secret: str) -> AccessToken:
    try:
        payload = jwt.decode(token, secret, algorithms=[_ALGORITHM])
        user_id = UUID(str(payload["sub"]))
        organization_id = UUID(str(payload["org"]))
    except (jwt.PyJWTError, KeyError, ValueError, TypeError) as exc:
        raise InvalidTokenError() from exc
    return AccessToken(user_id=user_id, organization_id=organization_id)
