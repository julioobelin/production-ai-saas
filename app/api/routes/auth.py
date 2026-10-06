from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, status

from app.api.deps import get_auth_service, get_current_user
from app.db.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.common import OrganizationRead
from app.schemas.user import UserRead
from app.services.auth import AuthService

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    body: RegisterRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    token = service.register(
        organization_name=body.organization_name,
        email=body.email,
        password=body.password,
        full_name=body.full_name,
    )
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    return TokenResponse(access_token=service.login(email=body.email, password=body.password))


@router.get("/me", response_model=UserRead)
def me(user: Annotated[User, Depends(get_current_user)]) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=cast(Literal["owner", "member"], user.role),
        organization=OrganizationRead(
            id=user.organization.id,
            name=user.organization.name,
            slug=user.organization.slug,
        ),
    )
