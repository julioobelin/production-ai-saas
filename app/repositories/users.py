from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.user import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(
        self,
        *,
        organization_id: uuid.UUID,
        email: str,
        password_hash: str,
        full_name: str,
        role: str,
    ) -> User:
        user = User(
            organization_id=organization_id,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
        )
        self._session.add(user)
        self._session.flush()
        return user

    def get(self, organization_id: uuid.UUID, user_id: uuid.UUID) -> User | None:
        statement = select(User).where(
            User.id == user_id,
            User.organization_id == organization_id,
        )
        return self._session.scalar(statement)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self._session.scalar(statement)

    def list_for_organization(
        self,
        organization_id: uuid.UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[User]:
        statement = (
            select(User)
            .where(User.organization_id == organization_id)
            .order_by(User.created_at, User.id)
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(statement).all())
