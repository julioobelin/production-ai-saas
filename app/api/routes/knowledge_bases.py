from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import get_current_user, get_knowledge_base_service, get_page_params
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.user import User
from app.schemas.common import Page, PageParams
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseRead, KnowledgeBaseUpdate
from app.services.knowledge_bases import KnowledgeBaseService

router = APIRouter()


@router.post("", response_model=KnowledgeBaseRead, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(
    body: KnowledgeBaseCreate,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)],
) -> KnowledgeBaseRead:
    knowledge_base = service.create(
        organization_id=user.organization_id,
        user_id=user.id,
        name=body.name,
        description=body.description,
    )
    return _read(knowledge_base)


@router.get("", response_model=Page[KnowledgeBaseRead])
def list_knowledge_bases(
    user: Annotated[User, Depends(get_current_user)],
    page: Annotated[PageParams, Depends(get_page_params)],
    service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)],
) -> Page[KnowledgeBaseRead]:
    rows = service.list(user.organization_id, limit=page.limit, offset=page.offset)
    return Page(items=[_read(row) for row in rows], limit=page.limit, offset=page.offset)


@router.get("/{knowledge_base_id}", response_model=KnowledgeBaseRead)
def get_knowledge_base(
    knowledge_base_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)],
) -> KnowledgeBaseRead:
    return _read(service.get(user.organization_id, knowledge_base_id))


@router.patch("/{knowledge_base_id}", response_model=KnowledgeBaseRead)
def update_knowledge_base(
    knowledge_base_id: UUID,
    body: KnowledgeBaseUpdate,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)],
) -> KnowledgeBaseRead:
    return _read(
        service.update(
            user.organization_id,
            knowledge_base_id,
            name=body.name,
            description=body.description,
        )
    )


@router.delete("/{knowledge_base_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_base(
    knowledge_base_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[KnowledgeBaseService, Depends(get_knowledge_base_service)],
) -> Response:
    service.delete(user.organization_id, knowledge_base_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _read(knowledge_base: KnowledgeBase) -> KnowledgeBaseRead:
    return KnowledgeBaseRead(
        id=knowledge_base.id,
        name=knowledge_base.name,
        description=knowledge_base.description,
        created_at=knowledge_base.created_at,
        updated_at=knowledge_base.updated_at,
    )
