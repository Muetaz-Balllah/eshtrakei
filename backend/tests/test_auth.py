from fastapi.testclient import TestClient


def test_login_me_and_logout(client: TestClient):
    login = client.post(
        "/api/auth/login",
        json={"email": "admin@eshtrakei.local", "password": "phase0-admin-pass"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["role"] == "platform_admin"
    logout = client.post("/api/auth/logout", headers=headers)
    assert logout.status_code == 200
    rejected = client.get("/api/auth/me", headers=headers)
    assert rejected.status_code == 401


def test_role_guard_rejects_client(client: TestClient):
    login = client.post(
        "/api/auth/login",
        json={"email": "client@eshtrakei.local", "password": "phase0-client-pass"},
    )
    token = login.json()["access_token"]
    response = client.get("/api/_phase0/admin-probe", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_health(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["database"] is True
    assert response.json()["redis"] is True
