from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_page_params, get_user_service, require_owner
from app.db.models.user import User
from app.schemas.common import Page, PageParams
from app.schemas.user import MemberRead, UserCreate
from app.services.users import UserService

router = APIRouter()


@router.get("", response_model=Page[MemberRead])
def list_users(
    user: Annotated[User, Depends(get_current_user)],
    page: Annotated[PageParams, Depends(get_page_params)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> Page[MemberRead]:
    members = service.list_members(user.organization_id, limit=page.limit, offset=page.offset)
    return Page(
        items=[_member(member) for member in members],
        limit=page.limit,
        offset=page.offset,
    )


@router.post("", response_model=MemberRead, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    user: Annotated[User, Depends(require_owner)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> MemberRead:
    member = service.create_member(
        organization_id=user.organization_id,
        email=body.email,
        password=body.password,
        full_name=body.full_name,
    )
    return _member(member)


def _member(user: User) -> MemberRead:
    return MemberRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=cast(Literal["owner", "member"], user.role),
        created_at=user.created_at,
    )
