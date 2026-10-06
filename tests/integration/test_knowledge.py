from sqlalchemy import text

from app.ai.providers.deterministic import NO_ANSWER
from app.api.deps import get_chat_provider
from app.main import app
from tests.fakes import RecordingChatProvider
from tests.helpers import bearer, register


def test_search_indexes_exist(db_session) -> None:
    names = set(
        db_session.execute(
            text("SELECT indexname FROM pg_indexes WHERE tablename = 'chunks'")
        ).scalars()
    )
    assert "ix_chunks_search_vector" in names
    assert "ix_chunks_embedding_hnsw" in names
    extension = db_session.scalar(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
    assert extension == "vector"


def test_question_is_grounded_and_the_conversation_is_stored(client) -> None:
    token = register(client)
    headers = bearer(token)
    knowledge_base = client.post(
        "/api/v1/knowledge-bases",
        headers=headers,
        json={"name": "Finance", "description": "Internal notes"},
    )
    assert knowledge_base.status_code == 201, knowledge_base.text
    knowledge_base_id = knowledge_base.json()["id"]

    document = client.post(
        f"/api/v1/knowledge-bases/{knowledge_base_id}/documents",
        headers=headers,
        json={
            "title": "Q3 finance note",
            "content": "Quarterly revenue was 10 million in the north region.",
        },
    )
    assert document.status_code == 201, document.text

    listed = client.get(
        f"/api/v1/knowledge-bases/{knowledge_base_id}/documents",
        headers=headers,
    )
    assert listed.status_code == 200
    assert "content" not in listed.json()["items"][0]
    fetched = client.get(
        f"/api/v1/knowledge-bases/{knowledge_base_id}/documents/{document.json()['id']}",
        headers=headers,
    )
    assert "10 million" in fetched.json()["content"]

    answer = client.post(
        f"/api/v1/knowledge-bases/{knowledge_base_id}/queries",
        headers=headers,
        json={"question": "What was quarterly revenue?"},
    )
    assert answer.status_code == 200, answer.text
    body = answer.json()
    assert body["provider"] == "deterministic"
    assert body["retrieval_mode"] == "lexical"
    assert body["citations"][0]["document_title"] == "Q3 finance note"
    assert "10 million" in body["citations"][0]["excerpt"]
    assert "Q3 finance note" in body["answer"]

    conversation = client.get(
        f"/api/v1/conversations/{body['conversation_id']}",
        headers=headers,
    )
    assert conversation.status_code == 200
    messages = conversation.json()["messages"]
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert messages[1]["provider"] == "deterministic"
    assert messages[1]["retrieval_mode"] == "lexical"
    assert messages[1]["citations"][0]["document_title"] == "Q3 finance note"

    follow_up = client.post(
        f"/api/v1/knowledge-bases/{knowledge_base_id}/queries",
        headers=headers,
        json={
            "question": "Which region was that?",
            "conversation_id": body["conversation_id"],
        },
    )
    assert follow_up.status_code == 200, follow_up.text
    stored = client.get(
        f"/api/v1/conversations/{body['conversation_id']}",
        headers=headers,
    )
    assert len(stored.json()["messages"]) == 4

    deleted = client.delete(
        f"/api/v1/conversations/{body['conversation_id']}",
        headers=headers,
    )
    assert deleted.status_code == 204
    missing = client.get(f"/api/v1/conversations/{body['conversation_id']}", headers=headers)
    assert missing.status_code == 404


def test_unknown_content_does_not_invent_an_answer(client) -> None:
    token = register(client)
    headers = bearer(token)
    knowledge_base = client.post(
        "/api/v1/knowledge-bases",
        headers=headers,
        json={"name": "Finance"},
    )
    knowledge_base_id = knowledge_base.json()["id"]
    client.post(
        f"/api/v1/knowledge-bases/{knowledge_base_id}/documents",
        headers=headers,
        json={"title": "Q3 finance note", "content": "Quarterly revenue was 10 million."},
    )
    response = client.post(
        f"/api/v1/knowledge-bases/{knowledge_base_id}/queries",
        headers=headers,
        json={"question": "submarine maintenance schedule"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["citations"] == []
    assert response.json()["answer"] == NO_ANSWER
    assert response.json()["retrieval_mode"] == "lexical"


def test_history_sent_to_the_provider_is_capped(client) -> None:
    token = register(client)
    headers = bearer(token)
    knowledge_base_id = client.post(
        "/api/v1/knowledge-bases",
        headers=headers,
        json={"name": "Finance"},
    ).json()["id"]
    client.post(
        f"/api/v1/knowledge-bases/{knowledge_base_id}/documents",
        headers=headers,
        json={"title": "Q3 finance note", "content": "Quarterly revenue was 10 million."},
    )
    recorder = RecordingChatProvider()
    app.dependency_overrides[get_chat_provider] = lambda: recorder
    conversation_id = None
    for index in range(5):
        payload: dict[str, object] = {"question": f"What was quarterly revenue? pass {index}"}
        if conversation_id is not None:
            payload["conversation_id"] = conversation_id
        response = client.post(
            f"/api/v1/knowledge-bases/{knowledge_base_id}/queries",
            headers=headers,
            json=payload,
        )
        assert response.status_code == 200, response.text
        conversation_id = response.json()["conversation_id"]
    last_call = recorder.calls[-1]
    history = last_call["history"]
    assert isinstance(history, list)
    assert len(history) == 6
    assert last_call["question"] == "What was quarterly revenue? pass 4"
    assert all(turn.content != last_call["question"] for turn in history)
    passages = last_call["passages"]
    assert isinstance(passages, list)
    assert passages[0].document_title == "Q3 finance note"


def test_knowledge_base_update_and_delete(client) -> None:
    token = register(client)
    headers = bearer(token)
    created = client.post(
        "/api/v1/knowledge-bases",
        headers=headers,
        json={"name": "Finance"},
    )
    knowledge_base_id = created.json()["id"]
    updated = client.patch(
        f"/api/v1/knowledge-bases/{knowledge_base_id}",
        headers=headers,
        json={"name": "Finance notes"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Finance notes"
    deleted = client.delete(f"/api/v1/knowledge-bases/{knowledge_base_id}", headers=headers)
    assert deleted.status_code == 204
    missing = client.get(f"/api/v1/knowledge-bases/{knowledge_base_id}", headers=headers)
    assert missing.status_code == 404
