from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import strip_string


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=50_000)

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value: object) -> object:
        return strip_string(value)


class DocumentRead(BaseModel):
    id: UUID
    knowledge_base_id: UUID
    title: str
    content: str
    created_at: datetime


class DocumentSummary(BaseModel):
    id: UUID
    knowledge_base_id: UUID
    title: str
    created_at: datetime
