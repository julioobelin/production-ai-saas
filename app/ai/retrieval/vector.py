"""pgvector retriever.

This is the only retrieval implementation that knows the column has a fixed
width. A dimension mismatch or a provider failure is returned to the caller.
This retriever does not fall back to lexical search.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.protocols import Embedder
from app.ai.types import Citation
from app.core.exceptions import EmbeddingsMissingError, ProviderError
from app.db.models.chunk import Chunk
from app.db.models.document import Document
from app.db.vector_schema import require_vector_dimension


class VectorRetriever:
    mode = "vector"

    def __init__(self, session: Session, embedder: Embedder) -> None:
        self._session = session
        self._embedder = embedder

    def search(
        self,
        *,
        organization_id: UUID,
        knowledge_base_id: UUID,
        query: str,
        limit: int,
    ) -> list[Citation]:
        total, embedded = self._counts(organization_id, knowledge_base_id)
        if total > 0 and embedded == 0:
            raise EmbeddingsMissingError()
        vectors = list(self._embedder.embed([query]))
        if len(vectors) != 1:
            raise ProviderError("The embedding provider returned an unexpected number of vectors")
        require_vector_dimension(vectors[0])
        distance = Chunk.embedding.cosine_distance(vectors[0])
        statement = (
            select(
                Chunk.id,
                Chunk.document_id,
                Document.title,
                Chunk.content,
                distance.label("distance"),
            )
            .join(Document, Document.id == Chunk.document_id)
            .where(Chunk.organization_id == organization_id)
            .where(Chunk.knowledge_base_id == knowledge_base_id)
            .where(Document.organization_id == organization_id)
            .where(Chunk.embedding.is_not(None))
            .order_by(distance, Chunk.id)
            .limit(limit)
        )
        rows = self._session.execute(statement).all()
        return [
            Citation(
                chunk_id=row.id,
                document_id=row.document_id,
                document_title=row.title,
                excerpt=row.content,
                score=round(1.0 - float(row.distance), 6),
            )
            for row in rows
        ]

    def _counts(self, organization_id: UUID, knowledge_base_id: UUID) -> tuple[int, int]:
        scope = (
            Chunk.organization_id == organization_id,
            Chunk.knowledge_base_id == knowledge_base_id,
        )
        total = self._session.scalar(select(func.count()).select_from(Chunk).where(*scope)) or 0
        embedded = (
            self._session.scalar(
                select(func.count()).select_from(Chunk).where(*scope, Chunk.embedding.is_not(None))
            )
            or 0
        )
        return int(total), int(embedded)
