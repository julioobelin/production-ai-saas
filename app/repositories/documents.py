from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models.document import Document


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(
        self,
        *,
        organization_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        title: str,
        content: str,
        created_by: uuid.UUID,
    ) -> Document:
        document = Document(
            organization_id=organization_id,
            knowledge_base_id=knowledge_base_id,
            title=title,
            content=content,
            created_by=created_by,
        )
        self._session.add(document)
        self._session.flush()
        return document

    def get(
        self,
        organization_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> Document | None:
        statement = select(Document).where(
            Document.id == document_id,
            Document.knowledge_base_id == knowledge_base_id,
            Document.organization_id == organization_id,
        )
        return self._session.scalar(statement)

    def list_for_knowledge_base(
        self,
        organization_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[Document]:
        statement = (
            select(Document)
            .where(
                Document.organization_id == organization_id,
                Document.knowledge_base_id == knowledge_base_id,
            )
            .order_by(Document.created_at.desc(), Document.id)
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(statement).all())

    def delete(
        self,
        organization_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> bool:
        result = self._session.execute(
            delete(Document).where(
                Document.id == document_id,
                Document.knowledge_base_id == knowledge_base_id,
                Document.organization_id == organization_id,
            )
        )
        return result.rowcount == 1
