import httpx
import pytest

from app.ai.providers.openai_compatible import (
    OpenAICompatibleChatProvider,
    OpenAICompatibleEmbedder,
)
from app.ai.types import ChatTurn, RetrievedPassage
from app.core.exceptions import ProviderError


def test_chat_request_sends_model_history_and_passages(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(url: str, *, json: dict, headers: dict, timeout: float) -> httpx.Response:
        captured["url"] = url
        captured["json"] = json
        captured["authorization"] = headers["Authorization"]
        captured["timeout"] = timeout
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Grounded answer"}}]},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    provider = OpenAICompatibleChatProvider(
        base_url="https://llm.test/v1/",
        api_key="test-key",
        model="chat-model",
        timeout_seconds=12,
    )
    answer = provider.complete(
        question="What changed?",
        history=[ChatTurn(role="user", content="Earlier question")],
        passages=[RetrievedPassage(document_title="Release notes", content="The API changed.")],
    )
    assert answer == "Grounded answer"
    assert captured["url"] == "https://llm.test/v1/chat/completions"
    assert captured["timeout"] == 12
    assert captured["authorization"] == "Bearer test-key"
    body = captured["json"]
    assert isinstance(body, dict)
    assert body["model"] == "chat-model"
    assert body["messages"][-1] == {"role": "user", "content": "What changed?"}
    assert "Release notes" in body["messages"][0]["content"]
    assert "The API changed." in body["messages"][0]["content"]
    assert {"role": "user", "content": "Earlier question"} in body["messages"]


def test_chat_failure_does_not_include_the_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_post(url: str, *, json: dict, headers: dict, timeout: float) -> httpx.Response:
        del json, headers, timeout
        return httpx.Response(
            503, json={"error": "unavailable"}, request=httpx.Request("POST", url)
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    provider = OpenAICompatibleChatProvider(
        base_url="https://llm.test/v1",
        api_key="test-key",
        model="chat-model",
        timeout_seconds=5,
    )
    with pytest.raises(ProviderError) as caught:
        provider.complete(question="What changed?", history=[], passages=[])
    assert "test-key" not in str(caught.value)


def test_embedder_sends_the_configured_model_and_omits_dimensions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_post(url: str, *, json: dict, headers: dict, timeout: float) -> httpx.Response:
        del headers, timeout
        captured["url"] = url
        captured["json"] = json
        payload = {
            "data": [
                {"index": 1, "embedding": [0.2, 0.3]},
                {"index": 0, "embedding": [0.0, 1.0]},
            ]
        }
        return httpx.Response(200, json=payload, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)
    embedder = OpenAICompatibleEmbedder(
        base_url="https://embed.test/v1",
        api_key="test-key",
        model="org/custom-embedder",
        timeout_seconds=5,
        dimensions=None,
    )
    vectors = embedder.embed(["first", "second"])
    assert vectors == [[0.0, 1.0], [0.2, 0.3]]
    body = captured["json"]
    assert isinstance(body, dict)
    assert body["model"] == "org/custom-embedder"
    assert "dimensions" not in body
    assert captured["url"] == "https://embed.test/v1/embeddings"


def test_embedder_forwards_dimensions_only_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(url: str, *, json: dict, headers: dict, timeout: float) -> httpx.Response:
        del url, headers, timeout
        captured["json"] = json
        return httpx.Response(
            200,
            json={"data": [{"index": 0, "embedding": [0.5]}]},
            request=httpx.Request("POST", "https://embed.test/v1/embeddings"),
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    embedder = OpenAICompatibleEmbedder(
        base_url="https://embed.test/v1",
        api_key="test-key",
        model="org/custom-embedder",
        timeout_seconds=5,
        dimensions=32,
    )
    assert embedder.embed(["once"]) == [[0.5]]
    assert captured["json"] == {
        "model": "org/custom-embedder",
        "input": ["once"],
        "dimensions": 32,
    }


def test_embedder_does_not_call_the_network_for_an_empty_batch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(*args: object, **kwargs: object) -> httpx.Response:
        del args, kwargs
        raise AssertionError("empty input must not be sent")

    monkeypatch.setattr(httpx, "post", fake_post)
    embedder = OpenAICompatibleEmbedder(
        base_url="https://embed.test/v1",
        api_key="test-key",
        model="org/custom-embedder",
        timeout_seconds=5,
        dimensions=None,
    )
    assert embedder.embed([]) == []
