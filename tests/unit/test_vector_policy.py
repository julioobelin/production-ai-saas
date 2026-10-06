from uuid import uuid4

import pytest

from app.core.exceptions import ProviderError, VectorDimensionError
from app.db.vector_schema import (
    SCHEMA_VECTOR_DIMENSIONS,
    assert_configured_dimensions,
    require_vector_dimension,
)
from app.services.documents import DocumentService


def test_wrong_vector_width_is_rejected() -> None:
    with pytest.raises(VectorDimensionError) as caught:
        require_vector_dimension([0.1, 0.2])
    assert caught.value.status_code == 503
    assert caught.value.code == "embedding_dimension_mismatch"
    assert str(SCHEMA_VECTOR_DIMENSIONS) in caught.value.message


def test_configured_width_must_match_the_column() -> None:
    assert_configured_dimensions(None)
    assert_configured_dimensions(SCHEMA_VECTOR_DIMENSIONS)
    with pytest.raises(ValueError):
        assert_configured_dimensions(SCHEMA_VECTOR_DIMENSIONS - 1)


def test_lexical_ingestion_does_not_call_the_embedder() -> None:
    chunks = _Chunks()
    service = _service(chunks, embedder=_ExplodingEmbedder(), retrieval_mode="lexical")
    service.create(
        organization_id=uuid4(),
        user_id=uuid4(),
        knowledge_base_id=uuid4(),
        title="Note",
        content="A short note.",
    )
    assert chunks.embeddings is None


def test_vector_ingestion_does_not_fall_back_when_the_embedder_fails() -> None:
    chunks = _Chunks()

    class Down:
        def embed(self, texts: list[str]) -> list[list[float]]:
            del texts
            raise ProviderError("down")

    service = _service(chunks, embedder=Down(), retrieval_mode="vector")
    with pytest.raises(ProviderError):
        service.create(
            organization_id=uuid4(),
            user_id=uuid4(),
            knowledge_base_id=uuid4(),
            title="Note",
            content="A short note.",
        )
    assert chunks.called is False


class _Chunks:
    def __init__(self) -> None:
        self.called = False
        self.embeddings: list[list[float]] | None = None

    def add_many(
        self, *, document: object, parts: list[str], embeddings: list[list[float]] | None
    ) -> None:
        del document, parts
        self.called = True
        self.embeddings = embeddings


class _ExplodingEmbedder:
    def embed(self, texts: list[str]) -> list[list[float]]:
        del texts
        raise AssertionError("lexical ingestion must not embed")


def _service(chunks: _Chunks, *, embedder: object, retrieval_mode: str) -> DocumentService:
    return DocumentService(
        documents=_Documents(),
        chunks=chunks,  # type: ignore[arg-type]
        knowledge_bases=_KnowledgeBases(),  # type: ignore[arg-type]
        embedder=embedder,  # type: ignore[arg-type]
        retrieval_mode=retrieval_mode,
        chunk_size=800,
        chunk_overlap=100,
        max_document_chars=50_000,
    )


class _Documents:
    def add(self, **kwargs: object) -> object:
        return type("Document", (), {"id": uuid4(), **kwargs})()


class _KnowledgeBases:
    def get(self, organization_id: object, knowledge_base_id: object) -> object:
        del organization_id, knowledge_base_id
        return object()
