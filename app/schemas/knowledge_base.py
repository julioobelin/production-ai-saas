from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.common import strip_string


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("name", "description", mode="before")
    @classmethod
    def strip_fields(cls, value: object) -> object:
        return strip_string(value)


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("name", "description", mode="before")
    @classmethod
    def strip_fields(cls, value: object) -> object:
        return strip_string(value)

    @model_validator(mode="after")
    def at_least_one_field(self) -> KnowledgeBaseUpdate:
        if self.name is None and self.description is None:
            raise ValueError("Provide a name or a description to update")
        return self


class KnowledgeBaseRead(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
