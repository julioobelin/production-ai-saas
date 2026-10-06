import pytest
from pydantic import ValidationError

from app.ai.factory import build_chat_provider, build_embedder, build_retriever
from app.ai.providers.deterministic import DeterministicGroundedProvider
from app.ai.providers.openai_compatible import OpenAICompatibleChatProvider
from app.ai.retrieval.lexical import LexicalRetriever
from app.ai.retrieval.vector import VectorRetriever
from app.core.config import Settings
from app.core.exceptions import ProviderError
from tests.fakes import FakeEmbedder

DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/knowledge_test"
JWT_SECRET = "test-jwt-secret-not-used-in-production-32"


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "environment": "test",
        "database_url": DATABASE_URL,
        "jwt_secret": JWT_SECRET,
        "llm_api_key": "",
        "embedding_api_key": "",
        "retrieval_mode": "lexical",
    }
    values.update(overrides)
    return Settings(**values)


def test_empty_llm_key_selects_the_deterministic_provider() -> None:
    provider = build_chat_provider(_settings())
    assert isinstance(provider, DeterministicGroundedProvider)
    assert provider.name == "deterministic"


def test_llm_key_selects_the_compatible_provider() -> None:
    provider = build_chat_provider(
        _settings(
            llm_api_key="test-key",
            llm_model="chat-model",
            llm_base_url="https://llm.test/v1",
        )
    )
    assert isinstance(provider, OpenAICompatibleChatProvider)
    assert provider.name == "openai_compatible"


def test_embedding_key_does_not_switch_lexical_retrieval() -> None:
    settings = _settings(
        retrieval_mode="lexical",
        embedding_api_key="test-key",
        embedding_model="custom-embedder",
        embedding_base_url="https://embed.test/v1",
    )
    embedder = build_embedder(settings)
    retriever = build_retriever(session=None, settings=settings, embedder=embedder)  # type: ignore[arg-type]
    assert isinstance(retriever, LexicalRetriever)
    assert retriever.mode == "lexical"


def test_vector_mode_selects_the_vector_retriever() -> None:
    settings = _settings(
        retrieval_mode="vector",
        embedding_api_key="test-key",
        embedding_model="custom-embedder",
        embedding_base_url="https://embed.test/v1",
    )
    retriever = build_retriever(session=None, settings=settings, embedder=FakeEmbedder())  # type: ignore[arg-type]
    assert isinstance(retriever, VectorRetriever)
    assert retriever.mode == "vector"


def test_vector_mode_without_an_embedder_fails() -> None:
    settings = _settings(
        retrieval_mode="vector",
        embedding_api_key="test-key",
        embedding_model="custom-embedder",
        embedding_base_url="https://embed.test/v1",
    )
    try:
        build_retriever(session=None, settings=settings, embedder=None)  # type: ignore[arg-type]
    except ProviderError as exc:
        assert exc.code == "provider_unavailable"
    else:
        raise AssertionError("vector mode without an embedder must fail")


def test_vector_mode_requires_embedding_settings() -> None:
    with pytest.raises(ValidationError):
        _settings(retrieval_mode="vector")


def test_production_rejects_the_placeholder_secret() -> None:
    with pytest.raises(ValidationError):
        _settings(
            environment="production",
            jwt_secret="replace-with-a-random-string-of-at-least-32-characters",
        )


def test_production_accepts_a_long_unlisted_secret() -> None:
    settings = _settings(
        environment="production",
        jwt_secret="a-unique-production-secret-value-32",
    )
    assert settings.environment == "production"
