from __future__ import annotations


def register(
    client,
    *,
    organization: str = "Northwind Studio",
    email: str = "ada@example.com",
    password: str = "correct-horse",
    full_name: str = "Ada Owner",
) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": organization,
            "email": email,
            "password": password,
            "full_name": full_name,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
