from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models.conversation import Conversation


class ConversationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(
        self,
        *,
        organization_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str,
    ) -> Conversation:
        conversation = Conversation(
            organization_id=organization_id,
            knowledge_base_id=knowledge_base_id,
            user_id=user_id,
            title=title,
        )
        self._session.add(conversation)
        self._session.flush()
        return conversation

    def get_for_user(
        self,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> Conversation | None:
        statement = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.organization_id == organization_id,
            Conversation.user_id == user_id,
        )
        return self._session.scalar(statement)

    def list_for_user(
        self,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[Conversation]:
        statement = (
            select(Conversation)
            .where(
                Conversation.organization_id == organization_id,
                Conversation.user_id == user_id,
            )
            .order_by(Conversation.created_at.desc(), Conversation.id)
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(statement).all())

    def delete(
        self,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> bool:
        result = self._session.execute(
            delete(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.organization_id == organization_id,
                Conversation.user_id == user_id,
            )
        )
        return result.rowcount == 1
