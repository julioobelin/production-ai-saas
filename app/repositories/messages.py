from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.message import Message


class MessageRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(
        self,
        *,
        organization_id: uuid.UUID,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        created_at: datetime,
        citations: list[dict[str, object]] | None = None,
        provider_name: str | None = None,
        retrieval_mode: str | None = None,
    ) -> Message:
        message = Message(
            organization_id=organization_id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            citations=citations,
            provider_name=provider_name,
            retrieval_mode=retrieval_mode,
            created_at=created_at,
        )
        self._session.add(message)
        self._session.flush()
        return message

    def list_for_conversation(
        self,
        organization_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> list[Message]:
        statement = (
            select(Message)
            .where(
                Message.organization_id == organization_id,
                Message.conversation_id == conversation_id,
            )
            .order_by(Message.created_at, Message.id)
        )
        return list(self._session.scalars(statement).all())

    def latest(
        self,
        organization_id: uuid.UUID,
        conversation_id: uuid.UUID,
        *,
        limit: int,
    ) -> list[Message]:
        """Return the newest messages, newest first."""

        statement = (
            select(Message)
            .where(
                Message.organization_id == organization_id,
                Message.conversation_id == conversation_id,
            )
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(limit)
        )
        return list(self._session.scalars(statement).all())
