from uuid import uuid4

import pytest

from app.core.exceptions import InvalidTokenError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

SECRET = "test-jwt-secret-not-used-in-production-32"


def test_password_hash_round_trip() -> None:
    stored = hash_password("correct-horse")
    assert stored != "correct-horse"
    assert stored.startswith("$argon2")
    assert verify_password("correct-horse", stored)
    assert not verify_password("wrong-password", stored)


def test_access_token_round_trip() -> None:
    user_id = uuid4()
    organization_id = uuid4()
    token = create_access_token(
        user_id=user_id,
        organization_id=organization_id,
        secret=SECRET,
        expires_minutes=30,
    )
    decoded = decode_access_token(token, SECRET)
    assert decoded.user_id == user_id
    assert decoded.organization_id == organization_id


def test_access_token_rejects_the_wrong_secret() -> None:
    token = create_access_token(
        user_id=uuid4(),
        organization_id=uuid4(),
        secret=SECRET,
        expires_minutes=30,
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(token, "another-secret-value-with-32-chars")


def test_access_token_rejects_expiry() -> None:
    expired = create_access_token(
        user_id=uuid4(),
        organization_id=uuid4(),
        secret=SECRET,
        expires_minutes=-1,
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(expired, SECRET)
