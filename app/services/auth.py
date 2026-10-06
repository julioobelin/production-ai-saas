from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, InvalidCredentialsError
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password_or_dummy,
)
from app.db.models.user import User
from app.repositories.organizations import OrganizationRepository
from app.repositories.users import UserRepository

OWNER = "owner"
MEMBER = "member"


class AuthService:
    def __init__(
        self,
        organizations: OrganizationRepository,
        users: UserRepository,
        *,
        jwt_secret: str,
        jwt_expire_minutes: int,
    ) -> None:
        self._organizations = organizations
        self._users = users
        self._jwt_secret = jwt_secret
        self._jwt_expire_minutes = jwt_expire_minutes

    def register(
        self,
        *,
        organization_name: str,
        email: str,
        password: str,
        full_name: str,
    ) -> str:
        if self._users.get_by_email(email) is not None:
            raise ConflictError("A user with this email already exists")
        try:
            organization = self._organizations.add(
                name=organization_name.strip(),
                slug=self._organizations.allocate_slug(organization_name),
            )
            user = self._users.add(
                organization_id=organization.id,
                email=email,
                password_hash=hash_password(password),
                full_name=full_name.strip(),
                role=OWNER,
            )
        except IntegrityError as exc:
            constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
            if constraint == "uq_organizations_slug":
                raise ConflictError("Could not allocate an organization slug") from exc
            raise ConflictError("A user with this email already exists") from exc
        return self._token(user)

    def login(self, *, email: str, password: str) -> str:
        user = self._users.get_by_email(email)
        if not verify_password_or_dummy(
            password,
            user.password_hash if user is not None else None,
        ):
            raise InvalidCredentialsError()
        if user is None:
            raise InvalidCredentialsError()
        return self._token(user)

    def _token(self, user: User) -> str:
        return create_access_token(
            user_id=user.id,
            organization_id=user.organization_id,
            secret=self._jwt_secret,
            expires_minutes=self._jwt_expire_minutes,
        )
