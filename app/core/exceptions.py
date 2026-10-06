"""Domain errors with a stable HTTP body."""

from __future__ import annotations


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication is required") -> None:
        super().__init__("unauthorized", message, 401)


class InvalidTokenError(AppError):
    def __init__(self) -> None:
        super().__init__("invalid_token", "Invalid or expired token", 401)


class InvalidCredentialsError(AppError):
    def __init__(self) -> None:
        super().__init__("invalid_credentials", "Invalid email or password", 401)


class ForbiddenError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__("forbidden", message, 403)


class NotFoundError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__("not_found", message, 404)


class ConflictError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__("conflict", message, 409)


class InvalidDocumentError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__("invalid_document", message, 422)


class EmbeddingsMissingError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "embeddings_missing",
            "This knowledge base has no embeddings. Re-ingest its documents with "
            "vector retrieval configured. Retrieval was not switched to lexical search.",
            409,
        )


class ProviderError(AppError):
    def __init__(self, message: str = "The model provider request failed") -> None:
        super().__init__("provider_unavailable", message, 503)


class VectorDimensionError(AppError):
    def __init__(self, *, actual: int, expected: int) -> None:
        super().__init__(
            "embedding_dimension_mismatch",
            f"The embedding provider returned {actual} dimensions, but the vector "
            f"column is fixed at {expected}. Retrieval was not switched to another mode. "
            "Use a model that returns that width, or plan a migration.",
            503,
        )


class DatabaseUnavailableError(AppError):
    def __init__(self) -> None:
        super().__init__("database_unavailable", "Database is not ready", 503)
