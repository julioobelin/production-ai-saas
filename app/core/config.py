"""Environment configuration. Business rules do not live here."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.security import INSECURE_JWT_SECRETS


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    database_url: str
    jwt_secret: str = Field(min_length=16)
    jwt_expire_minutes: int = Field(default=30, ge=1, le=1440)
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = ""
    llm_timeout_seconds: float = Field(default=30.0, gt=0, le=120)
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = ""
    embedding_dimensions: int | None = Field(default=None, ge=1)
    retrieval_mode: Literal["lexical", "vector"] = "lexical"
    retrieval_limit: int = Field(default=5, ge=1, le=20)
    chunk_size: int = Field(default=800, ge=200, le=4000)
    chunk_overlap: int = Field(default=100, ge=0, le=1000)
    max_document_chars: int = Field(default=50_000, ge=1, le=50_000)
    log_level: str = "INFO"

    @field_validator(
        "llm_api_key",
        "llm_model",
        "llm_base_url",
        "embedding_api_key",
        "embedding_model",
        "embedding_base_url",
    )
    @classmethod
    def strip_optional(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_runtime(self) -> Settings:
        if not self.database_url.startswith("postgresql+psycopg://"):
            raise ValueError("DATABASE_URL must use the postgresql+psycopg driver")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        if self.environment == "production":
            if len(self.jwt_secret) < 32 or self.jwt_secret in INSECURE_JWT_SECRETS:
                raise ValueError("JWT_SECRET is not acceptable for production")
        if self.llm_api_key and (not self.llm_model or not self.llm_base_url):
            raise ValueError("LLM_API_KEY requires LLM_MODEL and LLM_BASE_URL")
        if self.embedding_api_key and (not self.embedding_model or not self.embedding_base_url):
            raise ValueError("EMBEDDING_API_KEY requires EMBEDDING_MODEL and EMBEDDING_BASE_URL")
        if self.retrieval_mode == "vector" and (
            not self.embedding_api_key or not self.embedding_model or not self.embedding_base_url
        ):
            raise ValueError(
                "RETRIEVAL_MODE=vector requires EMBEDDING_API_KEY, "
                "EMBEDDING_MODEL, and EMBEDDING_BASE_URL"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
