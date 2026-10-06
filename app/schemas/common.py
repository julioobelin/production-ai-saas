from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


def strip_string(value: object) -> object:
    if isinstance(value, str):
        return value.strip()
    return value


class Page[T](BaseModel):
    items: list[T]
    limit: int
    offset: int


class PageParams(BaseModel):
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)


class OrganizationRead(BaseModel):
    id: UUID
    name: str
    slug: str
