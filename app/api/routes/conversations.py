from typing import Annotated, Literal, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import get_conversation_service, get_current_user, get_page_params
from app.db.models.message import Message
from app.db.models.user import User
from app.schemas.common import Page, PageParams
from app.schemas.conversation import ConversationDetail, ConversationRead, MessageRead
from app.schemas.query import CitationRead
from app.services.conversations import ConversationService

router = APIRouter()


@router.get("", response_model=Page[ConversationRead])
def list_conversations(
    user: Annotated[User, Depends(get_current_user)],
    page: Annotated[PageParams, Depends(get_page_params)],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> Page[ConversationRead]:
    rows = service.list(user.organization_id, user.id, limit=page.limit, offset=page.offset)
    return Page(
        items=[
            ConversationRead(
                id=row.id,
                knowledge_base_id=row.knowledge_base_id,
                title=row.title,
                created_at=row.created_at,
            )
            for row in rows
        ],
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> ConversationDetail:
    conversation, messages = service.get(user.organization_id, user.id, conversation_id)
    return ConversationDetail(
        id=conversation.id,
        knowledge_base_id=conversation.knowledge_base_id,
        title=conversation.title,
        created_at=conversation.created_at,
        messages=[_message(message) for message in messages],
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> Response:
    service.delete(user.organization_id, user.id, conversation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _message(message: Message) -> MessageRead:
    citations = None
    if message.citations is not None:
        citations = [CitationRead.model_validate(item) for item in message.citations]
    return MessageRead(
        id=message.id,
        role=cast(Literal["user", "assistant"], message.role),
        content=message.content,
        citations=citations,
        provider=message.provider_name,
        retrieval_mode=message.retrieval_mode,
        created_at=message.created_at,
    )
