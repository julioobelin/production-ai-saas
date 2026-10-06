"""PostgreSQL full-text retriever. It never calls an embedding provider."""

from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.types import Citation
from app.db.models.chunk import Chunk
from app.db.models.document import Document
from app.db.search_schema import FTS_REGCONFIG

_TOKEN = re.compile(r"\w+", flags=re.UNICODE)
_MAX_TERMS = 32


class LexicalRetriever:
    mode = "lexical"

    def __init__(self, session: Session) -> None:
        self._session = session

    def search(
        self,
        *,
        organization_id: UUID,
        knowledge_base_id: UUID,
        query: str,
        limit: int,
    ) -> list[Citation]:
        tsq = _question_to_tsquery(query)
        if tsq is None:
            return []
        rank = func.ts_rank_cd(Chunk.search_vector, tsq)
        statement = (
            select(Chunk.id, Chunk.document_id, Document.title, Chunk.content, rank.label("score"))
            .join(Document, Document.id == Chunk.document_id)
            .where(Chunk.organization_id == organization_id)
            .where(Chunk.knowledge_base_id == knowledge_base_id)
            .where(Document.organization_id == organization_id)
            .where(Chunk.search_vector.op("@@")(tsq))
            .order_by(rank.desc(), Chunk.id)
            .limit(limit)
        )
        rows = self._session.execute(statement).all()
        return [
            Citation(
                chunk_id=row.id,
                document_id=row.document_id,
                document_title=row.title,
                excerpt=row.content,
                score=round(float(row.score), 6),
            )
            for row in rows
        ]


def _question_to_tsquery(query: str):
    """Match any term. ``plainto_tsquery`` ANDs every word, which drops real questions."""

    terms = _TOKEN.findall(query)[:_MAX_TERMS]
    if not terms:
        return None
    return func.websearch_to_tsquery(FTS_REGCONFIG, " OR ".join(terms))
