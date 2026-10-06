from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.repositories.conversations import ConversationRepository
from app.repositories.messages import MessageRepository


class ConversationService:
    def __init__(
        self,
        conversations: ConversationRepository,
        messages: MessageRepository,
    ) -> None:
        self._conversations = conversations
        self._messages = messages

    def list(
        self,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[Conversation]:
        return self._conversations.list_for_user(
            organization_id,
            user_id,
            limit=limit,
            offset=offset,
        )

    def get(
        self,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> tuple[Conversation, list[Message]]:
        conversation = self._conversations.get_for_user(
            organization_id,
            user_id,
            conversation_id,
        )
        if conversation is None:
            raise NotFoundError("Conversation not found")
        messages = self._messages.list_for_conversation(organization_id, conversation.id)
        return conversation, messages

    def delete(
        self,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> None:
        if not self._conversations.delete(organization_id, user_id, conversation_id):
            raise NotFoundError("Conversation not found")
