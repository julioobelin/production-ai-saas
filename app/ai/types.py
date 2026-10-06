"""Values passed across the chat and retrieval ports."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ChatTurn:
    role: str
    content: str


@dataclass(frozen=True)
class RetrievedPassage:
    document_title: str
    content: str


@dataclass(frozen=True)
class Citation:
    chunk_id: UUID
    document_id: UUID
    document_title: str
    excerpt: str
    score: float
