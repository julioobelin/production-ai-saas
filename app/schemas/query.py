from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    conversation_id: UUID | None = None

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Question is empty")
        return stripped


class CitationRead(BaseModel):
    chunk_id: UUID
    document_id: UUID
    document_title: str
    excerpt: str
    score: float


class QueryResponse(BaseModel):
    conversation_id: UUID
    answer: str
    provider: str
    retrieval_mode: str
    citations: list[CitationRead]
