from __future__ import annotations

import uuid

from app.ai.chunking import chunk_text
from app.ai.protocols import Embedder
from app.core.exceptions import InvalidDocumentError, NotFoundError, ProviderError
from app.db.models.document import Document
from app.repositories.chunks import ChunkRepository
from app.repositories.documents import DocumentRepository
from app.repositories.knowledge_bases import KnowledgeBaseRepository


class DocumentService:
    def __init__(
        self,
        documents: DocumentRepository,
        chunks: ChunkRepository,
        knowledge_bases: KnowledgeBaseRepository,
        *,
        embedder: Embedder | None,
        retrieval_mode: str,
        chunk_size: int,
        chunk_overlap: int,
        max_document_chars: int,
    ) -> None:
        self._documents = documents
        self._chunks = chunks
        self._knowledge_bases = knowledge_bases
        self._embedder = embedder
        self._retrieval_mode = retrieval_mode
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._max_document_chars = max_document_chars

    def create(
        self,
        *,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        title: str,
        content: str,
    ) -> Document:
        if self._knowledge_bases.get(organization_id, knowledge_base_id) is None:
            raise NotFoundError("Knowledge base not found")
        text = content.strip()
        if not text:
            raise InvalidDocumentError("Document content is empty")
        if len(text) > self._max_document_chars:
            raise InvalidDocumentError("Document content is too long")
        parts = chunk_text(text, size=self._chunk_size, overlap=self._chunk_overlap)
        if not parts:
            raise InvalidDocumentError("Document content is empty")
        document = self._documents.add(
            organization_id=organization_id,
            knowledge_base_id=knowledge_base_id,
            title=title.strip(),
            content=text,
            created_by=user_id,
        )
        embeddings = self._embeddings_for(parts)
        self._chunks.add_many(document=document, parts=parts, embeddings=embeddings)
        return document

    def list(
        self,
        organization_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[Document]:
        if self._knowledge_bases.get(organization_id, knowledge_base_id) is None:
            raise NotFoundError("Knowledge base not found")
        return self._documents.list_for_knowledge_base(
            organization_id,
            knowledge_base_id,
            limit=limit,
            offset=offset,
        )

    def get(
        self,
        organization_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> Document:
        document = self._documents.get(organization_id, knowledge_base_id, document_id)
        if document is None:
            raise NotFoundError("Document not found")
        return document

    def delete(
        self,
        organization_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        document_id: uuid.UUID,
    ) -> None:
        if not self._documents.delete(organization_id, knowledge_base_id, document_id):
            raise NotFoundError("Document not found")

    def _embeddings_for(self, parts: list[str]) -> list[list[float]] | None:
        if self._retrieval_mode != "vector":
            return None
        if self._embedder is None:
            raise ProviderError("Vector retrieval is configured without an embedder")
        vectors = list(self._embedder.embed(parts))
        if len(vectors) != len(parts):
            raise ProviderError("The embedding provider returned an unexpected number of vectors")
        return vectors
