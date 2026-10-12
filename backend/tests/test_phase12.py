from fastapi.testclient import TestClient


def _auth(client: TestClient, email: str, password: str) -> dict:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_client_registers_and_role_cannot_escalate(client: TestClient):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "سارة أحمد",
            "city": "صنعاء",
            "phone": "777000111",
            "email": "sara@eshtrakei.local",
            "password": "password1",
            "role": "platform_admin",
        },
    )
    assert response.status_code == 200
    assert response.json()["role"] == "client"
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {response.json()['access_token']}"})
    assert me.json()["city"] == "صنعاء"
    assert me.json()["phone"] == "777000111"
    again = client.post(
        "/api/auth/register",
        json={
            "full_name": "سارة",
            "city": "عدن",
            "phone": "777",
            "email": "sara@eshtrakei.local",
            "password": "password1",
        },
    )
    assert again.status_code == 409
    short = client.post(
        "/api/auth/register",
        json={"full_name": "أ", "city": "عدن", "phone": "777", "email": "a@eshtrakei.local", "password": "short"},
    )
    assert short.status_code == 422
    letters = client.post(
        "/api/auth/register",
        json={"full_name": "أ", "city": "عدن", "phone": "777", "email": "letters@eshtrakei.local", "password": "abcdefgh"},
    )
    digits = client.post(
        "/api/auth/register",
        json={"full_name": "أ", "city": "عدن", "phone": "777", "email": "digits@eshtrakei.local", "password": "12345678"},
    )
    assert letters.status_code == 422
    assert digits.status_code == 422
    assert "حروف" in letters.json()["message"]


def test_join_approve_manager_stop_and_ads(client: TestClient):
    joined = client.post(
        "/api/join-requests",
        data={"name": "شركة النور", "description": "إنترنت منزلي", "phone": "012345"},
    )
    assert joined.status_code == 200
    request_id = joined.json()["id"]
    assert joined.json()["status"] == "pending"

    admin = _auth(client, "admin@eshtrakei.local", "phase0-admin-pass")
    approved = client.post(f"/api/admin/join-requests/{request_id}/approve", headers=admin)
    assert approved.status_code == 200
    company_id = approved.json()["id"]
    assert approved.status_code == 200

    created = client.post(
        f"/api/admin/companies/{company_id}/manager",
        headers=admin,
        json={"full_name": "ليلى", "email": "layla@eshtrakei.local", "password": "password1"},
    )
    assert created.status_code == 200
    second = client.post(
        f"/api/admin/companies/{company_id}/manager",
        headers=admin,
        json={"full_name": "أخرى", "email": "other@eshtrakei.local", "password": "password1"},
    )
    assert second.status_code == 409

    customer = client.post(
        "/api/auth/register",
        json={
            "full_name": "عميل",
            "city": "تعز",
            "phone": "700",
            "email": "client2@eshtrakei.local",
            "password": "password1",
        },
    )
    client_headers = {"Authorization": f"Bearer {customer.json()['access_token']}"}
    listed = client.get("/api/companies", headers=client_headers)
    assert any(row["name"] == "شركة النور" for row in listed.json())

    manager = _auth(client, "layla@eshtrakei.local", "password1")
    me = client.get("/api/company/me", headers=manager)
    assert me.status_code == 200
    assert me.json()["name"] == "شركة النور"
    ad = client.post("/api/company/advertisements", headers=manager, data={"title": "عرض الصيف", "body": "خصم"})
    assert ad.status_code == 200
    home = client.get("/api/advertisements", headers=client_headers)
    assert any(row["title"] == "عرض الصيف" for row in home.json())

    stopped = client.post(f"/api/admin/companies/{company_id}/stop", headers=admin)
    assert stopped.json()["status"] == "stopped"
    hidden = client.get("/api/companies", headers=client_headers)
    assert all(row["name"] != "شركة النور" for row in hidden.json())
    ads = client.get("/api/advertisements", headers=client_headers)
    assert all(row["title"] != "عرض الصيف" for row in ads.json())
    blocked = client.post("/api/auth/login", json={"email": "layla@eshtrakei.local", "password": "password1"})
    assert blocked.status_code == 403


def test_manager_cannot_open_admin_companies(client: TestClient):
    client.post("/api/join-requests", data={"name": "شركة ب", "description": "", "phone": "1"})
    admin = _auth(client, "admin@eshtrakei.local", "phase0-admin-pass")
    request_id = client.get("/api/admin/join-requests", headers=admin).json()[0]["id"]
    company_id = client.post(f"/api/admin/join-requests/{request_id}/approve", headers=admin).json()["id"]
    client.post(
        f"/api/admin/companies/{company_id}/manager",
        headers=admin,
        json={"full_name": "م", "email": "m@eshtrakei.local", "password": "password1"},
    )
    manager = _auth(client, "m@eshtrakei.local", "password1")
    assert client.get("/api/admin/companies", headers=manager).status_code == 403
