from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError
from app.core.security import hash_password
from app.db.models.user import User
from app.repositories.users import UserRepository
from app.services.auth import MEMBER


class UserService:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def list_members(
        self,
        organization_id: uuid.UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[User]:
        return self._users.list_for_organization(organization_id, limit=limit, offset=offset)

    def create_member(
        self,
        *,
        organization_id: uuid.UUID,
        email: str,
        password: str,
        full_name: str,
    ) -> User:
        if self._users.get_by_email(email) is not None:
            raise ConflictError("A user with this email already exists")
        try:
            return self._users.add(
                organization_id=organization_id,
                email=email,
                password_hash=hash_password(password),
                full_name=full_name.strip(),
                role=MEMBER,
            )
        except IntegrityError as exc:
            raise ConflictError("A user with this email already exists") from exc
