"""Test-only doubles. These are not retrieval implementations."""

from __future__ import annotations

from collections.abc import Sequence

from app.ai.types import ChatTurn, RetrievedPassage
from app.db.vector_schema import SCHEMA_VECTOR_DIMENSIONS


class FakeEmbedder:
    """Maps a couple of marker phrases onto orthogonal vectors of the schema width."""

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [_vector(text) for text in texts]


class RecordingChatProvider:
    name = "deterministic"

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def complete(
        self,
        *,
        question: str,
        history: Sequence[ChatTurn],
        passages: Sequence[RetrievedPassage],
    ) -> str:
        self.calls.append(
            {
                "question": question,
                "history": list(history),
                "passages": list(passages),
            }
        )
        return "recorded-answer"


def _vector(text: str) -> list[float]:
    vector = [0.0] * SCHEMA_VECTOR_DIMENSIONS
    lowered = text.lower()
    if "alpha-signal" in lowered:
        vector[0] = 1.0
    elif "beta-signal" in lowered:
        vector[1] = 1.0
    else:
        vector[2] = 1.0
    return vector
