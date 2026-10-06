from __future__ import annotations

# Environment is pinned before application imports so tests never read a developer key.
# ruff: noqa: E402
import os

os.environ["ENVIRONMENT"] = "test"
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/knowledge_test",
)
os.environ["JWT_SECRET"] = "test-jwt-secret-not-used-in-production-32"
os.environ["LLM_API_KEY"] = ""
os.environ["EMBEDDING_API_KEY"] = ""
os.environ["RETRIEVAL_MODE"] = "lexical"
os.environ["LLM_MODEL"] = ""
os.environ["EMBEDDING_MODEL"] = ""
os.environ["LLM_BASE_URL"] = "https://api.openai.com/v1"
os.environ["EMBEDDING_BASE_URL"] = "https://api.openai.com/v1"
os.environ.pop("EMBEDDING_DIMENSIONS", None)

from collections.abc import Iterator

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from alembic import command
from app.api.deps import get_embedder, get_settings
from app.core.config import get_settings as load_settings
from app.db.session import get_db
from app.main import app
from tests.fakes import FakeEmbedder

load_settings.cache_clear()


@pytest.fixture(scope="session")
def migrated_engine():
    url = os.environ["DATABASE_URL"]
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    engine = create_engine(url, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(migrated_engine) -> Iterator[Session]:
    connection = migrated_engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


def _bind_session(session: Session):
    def override() -> Iterator[Session]:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        else:
            session.commit()

    return override


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = _bind_session(db_session)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def vector_client(db_session: Session) -> Iterator[TestClient]:
    settings = load_settings().model_copy(
        update={
            "retrieval_mode": "vector",
            "embedding_api_key": "test-only",
            "embedding_model": "fake-embedder",
            "embedding_base_url": "http://embeddings.test/v1",
        }
    )
    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = _bind_session(db_session)
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_embedder] = lambda: FakeEmbedder()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
