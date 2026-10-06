"""Answers from retrieved passages only. Output is stable and does not use the network."""

from __future__ import annotations

from collections.abc import Sequence

from app.ai.types import ChatTurn, RetrievedPassage

NO_ANSWER = "The knowledge base does not contain an answer to this question."


class DeterministicGroundedProvider:
    name = "deterministic"

    def complete(
        self,
        *,
        question: str,
        history: Sequence[ChatTurn],
        passages: Sequence[RetrievedPassage],
    ) -> str:
        del question, history
        if not passages:
            return NO_ANSWER
        blocks = ["Based on the retrieved passages:"]
        for index, passage in enumerate(passages, start=1):
            blocks.append(f"[{index}] {passage.document_title}\n{passage.content}")
        return "\n\n".join(blocks)
