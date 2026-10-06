from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.chunk import Chunk
from app.db.models.document import Document
from app.db.vector_schema import require_vector_dimension


class ChunkRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_many(
        self,
        *,
        document: Document,
        parts: list[str],
        embeddings: list[list[float]] | None,
    ) -> None:
        if embeddings is not None:
            for vector in embeddings:
                require_vector_dimension(vector)
        rows = [
            Chunk(
                organization_id=document.organization_id,
                knowledge_base_id=document.knowledge_base_id,
                document_id=document.id,
                position=position,
                content=content,
                embedding=None if embeddings is None else embeddings[position],
            )
            for position, content in enumerate(parts)
        ]
        self._session.add_all(rows)
        self._session.flush()
