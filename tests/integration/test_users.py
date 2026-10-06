from tests.helpers import bearer, register


def test_owner_creates_a_member_and_a_member_cannot(client) -> None:
    owner = register(client)
    created = client.post(
        "/api/v1/users",
        headers=bearer(owner),
        json={
            "email": "grace@example.com",
            "password": "correct-horse",
            "full_name": "Grace Member",
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["role"] == "member"
    assert "$argon2" not in created.text

    members = client.get("/api/v1/users", headers=bearer(owner))
    assert members.status_code == 200
    emails = {item["email"] for item in members.json()["items"]}
    assert emails == {"ada@example.com", "grace@example.com"}

    logged_in = client.post(
        "/api/v1/auth/login",
        json={"email": "grace@example.com", "password": "correct-horse"},
    )
    member = logged_in.json()["access_token"]
    visible = client.get("/api/v1/users", headers=bearer(member))
    assert visible.status_code == 200

    rejected = client.post(
        "/api/v1/users",
        headers=bearer(member),
        json={
            "email": "other@example.com",
            "password": "correct-horse",
            "full_name": "Other Person",
        },
    )
    assert rejected.status_code == 403
    assert rejected.json()["error"]["code"] == "forbidden"
