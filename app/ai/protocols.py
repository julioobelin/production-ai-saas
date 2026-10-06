"""Ports for chat, embeddings, and retrieval."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from app.ai.types import ChatTurn, Citation, RetrievedPassage


class ChatProvider(Protocol):
    name: str

    def complete(
        self,
        *,
        question: str,
        history: Sequence[ChatTurn],
        passages: Sequence[RetrievedPassage],
    ) -> str: ...


class Embedder(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class Retriever(Protocol):
    mode: str

    def search(
        self,
        *,
        organization_id: UUID,
        knowledge_base_id: UUID,
        query: str,
        limit: int,
    ) -> list[Citation]: ...
