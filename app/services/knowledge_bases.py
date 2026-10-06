from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.db.models.knowledge_base import KnowledgeBase
from app.repositories.knowledge_bases import KnowledgeBaseRepository


class KnowledgeBaseService:
    def __init__(self, knowledge_bases: KnowledgeBaseRepository) -> None:
        self._knowledge_bases = knowledge_bases

    def create(
        self,
        *,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        name: str,
        description: str | None,
    ) -> KnowledgeBase:
        return self._knowledge_bases.add(
            organization_id=organization_id,
            name=name.strip(),
            description=description.strip() if description else None,
            created_by=user_id,
        )

    def list(
        self,
        organization_id: uuid.UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[KnowledgeBase]:
        return self._knowledge_bases.list_for_organization(
            organization_id,
            limit=limit,
            offset=offset,
        )

    def get(self, organization_id: uuid.UUID, knowledge_base_id: uuid.UUID) -> KnowledgeBase:
        knowledge_base = self._knowledge_bases.get(organization_id, knowledge_base_id)
        if knowledge_base is None:
            raise NotFoundError("Knowledge base not found")
        return knowledge_base

    def update(
        self,
        organization_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        *,
        name: str | None,
        description: str | None,
    ) -> KnowledgeBase:
        knowledge_base = self.get(organization_id, knowledge_base_id)
        if name is not None:
            knowledge_base.name = name.strip()
        if description is not None:
            knowledge_base.description = description.strip() or None
        self._knowledge_bases.flush()
        return knowledge_base

    def delete(self, organization_id: uuid.UUID, knowledge_base_id: uuid.UUID) -> None:
        if not self._knowledge_bases.delete(organization_id, knowledge_base_id):
            raise NotFoundError("Knowledge base not found")
