from tests.helpers import bearer, register


def test_another_organization_cannot_see_resources(client) -> None:
    owner_a = register(client, organization="Alpha Studio", email="alpha@example.com")
    owner_b = register(client, organization="Beta Studio", email="beta@example.com")
    headers_a = bearer(owner_a)
    headers_b = bearer(owner_b)

    knowledge_base = client.post(
        "/api/v1/knowledge-bases",
        headers=headers_a,
        json={"name": "Policies"},
    )
    knowledge_base_id = knowledge_base.json()["id"]
    document = client.post(
        f"/api/v1/knowledge-bases/{knowledge_base_id}/documents",
        headers=headers_a,
        json={"title": "Policy", "content": "Visitors sign in at the front desk."},
    )
    document_id = document.json()["id"]
    answer = client.post(
        f"/api/v1/knowledge-bases/{knowledge_base_id}/queries",
        headers=headers_a,
        json={"question": "Where do visitors sign in?"},
    )
    conversation_id = answer.json()["conversation_id"]

    assert (
        client.get(
            f"/api/v1/knowledge-bases/{knowledge_base_id}",
            headers=headers_b,
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}",
            headers=headers_b,
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/v1/knowledge-bases/{knowledge_base_id}/queries",
            headers=headers_b,
            json={"question": "Where do visitors sign in?"},
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/v1/conversations/{conversation_id}",
            headers=headers_b,
        ).status_code
        == 404
    )

    member = client.post(
        "/api/v1/users",
        headers=headers_a,
        json={
            "email": "member@example.com",
            "password": "correct-horse",
            "full_name": "Alpha Member",
        },
    )
    assert member.status_code == 201
    member_token = client.post(
        "/api/v1/auth/login",
        json={"email": "member@example.com", "password": "correct-horse"},
    ).json()["access_token"]
    shared = client.get(
        f"/api/v1/knowledge-bases/{knowledge_base_id}",
        headers=bearer(member_token),
    )
    assert shared.status_code == 200
    hidden_conversation = client.get(
        f"/api/v1/conversations/{conversation_id}",
        headers=bearer(member_token),
    )
    assert hidden_conversation.status_code == 404
