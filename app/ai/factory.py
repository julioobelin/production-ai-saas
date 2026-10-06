"""Select provider implementations from settings. This is wiring, not a business rule."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.protocols import ChatProvider, Embedder, Retriever
from app.ai.providers.deterministic import DeterministicGroundedProvider
from app.ai.providers.openai_compatible import (
    OpenAICompatibleChatProvider,
    OpenAICompatibleEmbedder,
)
from app.ai.retrieval.lexical import LexicalRetriever
from app.ai.retrieval.vector import VectorRetriever
from app.core.config import Settings
from app.core.exceptions import ProviderError


def build_chat_provider(settings: Settings) -> ChatProvider:
    if not settings.llm_api_key:
        return DeterministicGroundedProvider()
    return OpenAICompatibleChatProvider(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
    )


def build_embedder(settings: Settings) -> Embedder | None:
    if not settings.embedding_api_key:
        return None
    return OpenAICompatibleEmbedder(
        base_url=settings.embedding_base_url,
        api_key=settings.embedding_api_key,
        model=settings.embedding_model,
        timeout_seconds=settings.llm_timeout_seconds,
        dimensions=settings.embedding_dimensions,
    )


def build_retriever(session: Session, settings: Settings, embedder: Embedder | None) -> Retriever:
    if settings.retrieval_mode == "vector":
        if embedder is None:
            raise ProviderError("Vector retrieval is configured without an embedder")
        return VectorRetriever(session, embedder)
    return LexicalRetriever(session)
