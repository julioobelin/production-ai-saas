"""Fixed width of the pgvector column.

PostgreSQL can store vectors of unequal length, but an HNSW index cannot.
This deployment therefore picks one width when the table is created.
Application services never read this value and never name an embedding vendor.
An embedder that returns a different width fails the request. Changing the
width is a new migration, not a runtime setting.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.core.exceptions import VectorDimensionError

SCHEMA_VECTOR_DIMENSIONS = 1536


def require_vector_dimension(vector: Sequence[float]) -> None:
    actual = len(vector)
    if actual != SCHEMA_VECTOR_DIMENSIONS:
        raise VectorDimensionError(actual=actual, expected=SCHEMA_VECTOR_DIMENSIONS)


def assert_configured_dimensions(dimensions: int | None) -> None:
    """Reject a configured width that cannot fit the column.

    ``None`` means the embedding request will not ask the provider to resize
    its output. The returned vector is still checked on write.
    """

    if dimensions is None:
        return
    if dimensions != SCHEMA_VECTOR_DIMENSIONS:
        raise ValueError(
            "EMBEDDING_DIMENSIONS is "
            f"{dimensions}, but the vector column width is {SCHEMA_VECTOR_DIMENSIONS}. "
            "That width is fixed by migration. Choose a model that returns it, "
            "or set EMBEDDING_DIMENSIONS only when the endpoint can emit that width."
        )
