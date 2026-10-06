"""HTTP clients for OpenAI-compatible chat and embedding endpoints.

The model name, base URL, and optional output width come from configuration.
This module does not assume a vendor's default vector size.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

import httpx

from app.ai.types import ChatTurn, RetrievedPassage
from app.core.exceptions import ProviderError

logger = logging.getLogger("app.provider")

_BATCH_SIZE = 64


class OpenAICompatibleChatProvider:
    name = "openai_compatible"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_seconds

    def complete(
        self,
        *,
        question: str,
        history: Sequence[ChatTurn],
        passages: Sequence[RetrievedPassage],
    ) -> str:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": _system_prompt(passages)},
        ]
        for turn in history:
            if turn.role in {"user", "assistant"}:
                messages.append({"role": turn.role, "content": turn.content})
        messages.append({"role": "user", "content": question})
        body = self._post(
            f"{self._base_url}/chat/completions",
            {"model": self._model, "messages": messages},
        )
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("The language model returned an unexpected response") from exc
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("The language model returned an empty answer")
        return content

    def _post(self, url: str, payload: dict[str, object]) -> dict[str, object]:
        return _post_json(
            url,
            payload,
            api_key=self._api_key,
            timeout=self._timeout,
            failure="The language model request failed",
        )


class OpenAICompatibleEmbedder:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
        dimensions: int | None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_seconds
        self._dimensions = dimensions

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        items = list(texts)
        if not items:
            return []
        vectors: list[list[float]] = []
        for start in range(0, len(items), _BATCH_SIZE):
            vectors.extend(self._embed_batch(items[start : start + _BATCH_SIZE]))
        return vectors

    def _embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        payload: dict[str, object] = {"model": self._model, "input": list(texts)}
        if self._dimensions is not None:
            payload["dimensions"] = self._dimensions
        body = self._post(f"{self._base_url}/embeddings", payload)
        try:
            rows = body["data"]
            ordered = sorted(rows, key=lambda item: item["index"])
            vectors = [row["embedding"] for row in ordered]
        except (KeyError, TypeError) as exc:
            raise ProviderError("The embedding provider returned an unexpected response") from exc
        if len(vectors) != len(texts) or any(not isinstance(vector, list) for vector in vectors):
            raise ProviderError("The embedding provider returned an unexpected number of vectors")
        return vectors

    def _post(self, url: str, payload: dict[str, object]) -> dict[str, object]:
        return _post_json(
            url,
            payload,
            api_key=self._api_key,
            timeout=self._timeout,
            failure="The embedding provider request failed",
        )


def _post_json(
    url: str,
    payload: dict[str, object],
    *,
    api_key: str,
    timeout: float,
    failure: str,
) -> dict[str, object]:
    try:
        response = httpx.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )
        response.raise_for_status()
        body = response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "provider_request_failed",
            extra={"event": "provider_request_failed", "status_code": exc.response.status_code},
        )
        raise ProviderError(failure) from None
    except httpx.HTTPError:
        logger.warning("provider_request_failed", extra={"event": "provider_request_failed"})
        raise ProviderError(failure) from None
    except ValueError:
        raise ProviderError(failure) from None
    if not isinstance(body, dict):
        raise ProviderError(failure)
    return body


def _system_prompt(passages: Sequence[RetrievedPassage]) -> str:
    if not passages:
        return (
            "You answer questions about a private knowledge base. "
            "No passages were retrieved. Say that the knowledge base does not contain an answer. "
            "Do not use outside knowledge."
        )
    lines = [
        "You answer questions about a private knowledge base. "
        "Use only the passages below. If they do not contain the answer, say so. "
        "Do not invent sources.",
        "",
        "Passages:",
    ]
    for index, passage in enumerate(passages, start=1):
        lines.append(f"[{index}] {passage.document_title}")
        lines.append(passage.content)
        lines.append("")
    return "\n".join(lines).strip()
