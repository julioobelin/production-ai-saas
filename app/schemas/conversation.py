from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.query import CitationRead


class MessageRead(BaseModel):
    id: UUID
    role: Literal["user", "assistant"]
    content: str
    citations: list[CitationRead] | None
    provider: str | None
    retrieval_mode: str | None
    created_at: datetime


class ConversationRead(BaseModel):
    id: UUID
    knowledge_base_id: UUID
    title: str
    created_at: datetime


class ConversationDetail(ConversationRead):
    messages: list[MessageRead]
