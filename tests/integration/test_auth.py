from tests.helpers import bearer, register


def test_health_and_ready(client) -> None:
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert health.headers["x-request-id"]

    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json() == {"status": "ok"}


def test_register_login_and_me(client) -> None:
    token = register(client)
    me = client.get("/api/v1/auth/me", headers=bearer(token))
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "ada@example.com"
    assert body["role"] == "owner"
    assert body["organization"]["slug"] == "northwind-studio"
    assert "password" not in me.text
    assert "$argon2" not in me.text

    logged_in = client.post(
        "/api/v1/auth/login",
        json={"email": "Ada@Example.com", "password": "correct-horse"},
    )
    assert logged_in.status_code == 200
    again = client.get("/api/v1/auth/me", headers=bearer(logged_in.json()["access_token"]))
    assert again.status_code == 200
    assert again.json()["id"] == body["id"]


def test_missing_and_invalid_tokens_are_rejected(client) -> None:
    missing = client.get("/api/v1/auth/me")
    assert missing.status_code == 401
    assert missing.json()["error"]["code"] == "unauthorized"

    invalid = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-token"})
    assert invalid.status_code == 401
    assert invalid.json()["error"]["code"] == "unauthorized"


def test_duplicate_email_conflicts(client) -> None:
    register(client, email="ada@example.com")
    response = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Other Studio",
            "email": "ada@example.com",
            "password": "correct-horse",
            "full_name": "Ada Again",
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_wrong_password_is_rejected(client) -> None:
    register(client)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ada@example.com", "password": "not-the-password"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_validation_error_does_not_echo_the_password(client) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Northwind Studio",
            "email": "ada@example.com",
            "password": "1234567",
            "full_name": "Ada Owner",
        },
    )
    assert response.status_code == 422
    assert "1234567" not in response.text
