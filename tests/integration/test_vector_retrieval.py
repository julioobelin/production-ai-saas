from sqlalchemy import update

from app.db.models.chunk import Chunk
from tests.helpers import bearer, register


def test_vector_retrieval_orders_by_the_injected_embedder(vector_client) -> None:
    token = register(vector_client, email="ada@example.com")
    headers = bearer(token)
    knowledge_base_id = vector_client.post(
        "/api/v1/knowledge-bases",
        headers=headers,
        json={"name": "Signals"},
    ).json()["id"]
    vector_client.post(
        f"/api/v1/knowledge-bases/{knowledge_base_id}/documents",
        headers=headers,
        json={"title": "Beta note", "content": "beta-signal facilities checklist"},
    )
    vector_client.post(
        f"/api/v1/knowledge-bases/{knowledge_base_id}/documents",
        headers=headers,
        json={"title": "Alpha note", "content": "alpha-signal quarterly notes"},
    )
    response = vector_client.post(
        f"/api/v1/knowledge-bases/{knowledge_base_id}/queries",
        headers=headers,
        json={"question": "Tell me about the alpha-signal"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["retrieval_mode"] == "vector"
    assert body["provider"] == "deterministic"
    assert body["citations"][0]["document_title"] == "Alpha note"
    assert body["citations"][0]["score"] > body["citations"][1]["score"]


def test_vector_mode_does_not_fall_back_when_embeddings_are_missing(
    vector_client, db_session
) -> None:
    token = register(vector_client, email="ada@example.com")
    headers = bearer(token)
    knowledge_base_id = vector_client.post(
        "/api/v1/knowledge-bases",
        headers=headers,
        json={"name": "Signals"},
    ).json()["id"]
    created = vector_client.post(
        f"/api/v1/knowledge-bases/{knowledge_base_id}/documents",
        headers=headers,
        json={"title": "Alpha note", "content": "alpha-signal quarterly notes"},
    )
    assert created.status_code == 201, created.text
    db_session.execute(update(Chunk).values(embedding=None))
    db_session.commit()
    response = vector_client.post(
        f"/api/v1/knowledge-bases/{knowledge_base_id}/queries",
        headers=headers,
        json={"question": "Tell me about the alpha-signal"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "embeddings_missing"
    assert "lexical" in response.json()["error"]["message"]
