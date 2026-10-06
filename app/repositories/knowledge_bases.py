from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models.knowledge_base import KnowledgeBase


class KnowledgeBaseRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(
        self,
        *,
        organization_id: uuid.UUID,
        name: str,
        description: str | None,
        created_by: uuid.UUID,
    ) -> KnowledgeBase:
        knowledge_base = KnowledgeBase(
            organization_id=organization_id,
            name=name,
            description=description,
            created_by=created_by,
        )
        self._session.add(knowledge_base)
        self._session.flush()
        return knowledge_base

    def get(
        self,
        organization_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
    ) -> KnowledgeBase | None:
        statement = select(KnowledgeBase).where(
            KnowledgeBase.id == knowledge_base_id,
            KnowledgeBase.organization_id == organization_id,
        )
        return self._session.scalar(statement)

    def list_for_organization(
        self,
        organization_id: uuid.UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[KnowledgeBase]:
        statement = (
            select(KnowledgeBase)
            .where(KnowledgeBase.organization_id == organization_id)
            .order_by(KnowledgeBase.created_at.desc(), KnowledgeBase.id)
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(statement).all())

    def flush(self) -> None:
        self._session.flush()

    def delete(self, organization_id: uuid.UUID, knowledge_base_id: uuid.UUID) -> bool:
        result = self._session.execute(
            delete(KnowledgeBase).where(
                KnowledgeBase.id == knowledge_base_id,
                KnowledgeBase.organization_id == organization_id,
            )
        )
        return result.rowcount == 1
