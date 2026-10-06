from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import get_current_user, get_document_service, get_page_params
from app.db.models.document import Document
from app.db.models.user import User
from app.schemas.common import Page, PageParams
from app.schemas.document import DocumentCreate, DocumentRead, DocumentSummary
from app.services.documents import DocumentService

router = APIRouter()


@router.post(
    "/{knowledge_base_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_document(
    knowledge_base_id: UUID,
    body: DocumentCreate,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentRead:
    document = service.create(
        organization_id=user.organization_id,
        user_id=user.id,
        knowledge_base_id=knowledge_base_id,
        title=body.title,
        content=body.content,
    )
    return _read(document)


@router.get("/{knowledge_base_id}/documents", response_model=Page[DocumentSummary])
def list_documents(
    knowledge_base_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    page: Annotated[PageParams, Depends(get_page_params)],
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> Page[DocumentSummary]:
    rows = service.list(
        user.organization_id,
        knowledge_base_id,
        limit=page.limit,
        offset=page.offset,
    )
    return Page(
        items=[_summary(row) for row in rows],
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/{knowledge_base_id}/documents/{document_id}", response_model=DocumentRead)
def get_document(
    knowledge_base_id: UUID,
    document_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentRead:
    return _read(service.get(user.organization_id, knowledge_base_id, document_id))


@router.delete(
    "/{knowledge_base_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_document(
    knowledge_base_id: UUID,
    document_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> Response:
    service.delete(user.organization_id, knowledge_base_id, document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _read(document: Document) -> DocumentRead:
    return DocumentRead(
        id=document.id,
        knowledge_base_id=document.knowledge_base_id,
        title=document.title,
        content=document.content,
        created_at=document.created_at,
    )


def _summary(document: Document) -> DocumentSummary:
    return DocumentSummary(
        id=document.id,
        knowledge_base_id=document.knowledge_base_id,
        title=document.title,
        created_at=document.created_at,
    )
