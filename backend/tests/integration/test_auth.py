from fastapi.testclient import TestClient


def authorization_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_protected_endpoint_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/users")

    assert response.status_code == 401


def test_login_and_current_user(client: TestClient) -> None:
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "test-admin-password"},
    )

    assert login.status_code == 200
    payload = login.json()
    assert payload["token_type"] == "bearer"
    assert payload["user"]["roles"] == ["ADMINISTRADOR"]

    me = client.get("/api/v1/auth/me", headers=authorization_header(payload["access_token"]))
    assert me.status_code == 200
    assert me.json()["username"] == "admin"


def test_login_rejects_invalid_password(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["error"] == "authentication_error"


def test_refresh_token_is_rotated(client: TestClient) -> None:
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "test-admin-password"},
    )
    original_cookie = login.cookies.get("reee_refresh_token")

    refreshed = client.post("/api/v1/auth/refresh")

    assert refreshed.status_code == 200
    assert refreshed.cookies.get("reee_refresh_token") != original_cookie
    assert refreshed.json()["access_token"] != login.json()["access_token"]


def test_rbac_blocks_auditor_from_user_management(client: TestClient, admin_token: str) -> None:
    created = client.post(
        "/api/v1/users",
        headers=authorization_header(admin_token),
        json={
            "username": "auditor-test",
            "email": "auditor@example.com",
            "full_name": "Auditor de testes",
            "password": "auditor-password-123",
            "role_codes": ["AUDITOR"],
        },
    )
    assert created.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        data={"username": "auditor-test", "password": "auditor-password-123"},
    )
    response = client.get(
        "/api/v1/users",
        headers=authorization_header(login.json()["access_token"]),
    )

    assert response.status_code == 403
    assert response.json()["error"] == "authorization_error"


def test_auditor_can_read_audit_log(client: TestClient, admin_token: str) -> None:
    response = client.get("/api/v1/audit-logs", headers=authorization_header(admin_token))

    assert response.status_code == 200
    assert any(log["action"] == "auth.login" for log in response.json())

