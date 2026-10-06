from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.common import OrganizationRead, strip_string


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=200)

    @field_validator("full_name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        return strip_string(value)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: Literal["owner", "member"]
    organization: OrganizationRead


class MemberRead(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: Literal["owner", "member"]
    created_at: datetime
