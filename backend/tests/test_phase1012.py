from fastapi.testclient import TestClient


def _login(client: TestClient, email: str, password: str) -> dict:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_reports_performance_and_settings(client: TestClient):
    admin = _login(client, "admin@eshtrakei.local", "phase0-admin-pass")
    settings = client.get("/api/admin/settings", headers=admin)
    assert settings.status_code == 200
    assert settings.json()["platform_commission_percentage"] == 5.0
    assert client.get("/api/admin/settings").status_code == 401

    joined = client.post("/api/join-requests", data={"name": "شركة الأرباح", "description": "نت", "phone": "091"})
    company_id = client.post(f"/api/admin/join-requests/{joined.json()['id']}/approve", headers=admin).json()["id"]
    client.post(
        f"/api/admin/companies/{company_id}/manager",
        headers=admin,
        json={"full_name": "محاسب", "email": "finance@eshtrakei.local", "password": "password1"},
    )
    manager = _login(client, "finance@eshtrakei.local", "password1")
    package_id = client.post(
        "/api/company/packages",
        headers=manager,
        json={"name": "باقة", "price": "200", "duration_amount": 30, "duration_unit": "days", "data_gb": 20, "speed_mbps": 10},
    ).json()["id"]
    buyer = client.post(
        "/api/auth/register",
        json={"full_name": "زبون", "city": "بنغازي", "phone": "092", "email": "buyer2@eshtrakei.local", "password": "password1"},
    )
    buyer_headers = {"Authorization": f"Bearer {buyer.json()['access_token']}"}
    client.post(
        "/api/subscriptions/purchases",
        headers=buyer_headers,
        json={"company_id": company_id, "package_id": package_id, "idempotency_key": "profit-key-01", "simulated_outcome": "success"},
    )
    client.post(
        "/api/subscriptions/purchases",
        headers=buyer_headers,
        json={"company_id": company_id, "package_id": package_id, "idempotency_key": "profit-fail-01", "simulated_outcome": "failure"},
    )
    report = client.get("/api/company/reports/sales", headers=manager).json()
    assert report["sales_total"] == "200.00"
    assert report["profit_total"] == "190.00"
    assert len(report["sales"]) == 1
    assert client.get("/api/company/reports/sales", headers=buyer_headers).status_code == 403

    performance = client.get("/api/admin/performance", headers=admin).json()
    assert performance["total_gross_sales"] == "200.00"
    assert performance["total_platform_net_revenue"] == "10.00"
    assert performance["total_active_companies"] == 1
    assert performance["total_registered_clients"] >= 1
    assert performance["total_active_subscriptions"] == 1
    assert client.get("/api/admin/performance", headers=manager).status_code == 403

    support = client.get("/api/settings/support-email", headers=buyer_headers).json()
    assert support["support_email"] == "support@platform.ly"
    closed = client.put(
        "/api/admin/settings",
        headers=admin,
        json={
            "platform_commission_percentage": 5,
            "allow_company_registration": False,
            "expiry_warning_days": [3, 1],
            "support_email": "support@platform.ly",
        },
    )
    assert closed.status_code == 200
    paused = client.post("/api/join-requests", data={"name": "شركة جديدة", "description": "", "phone": "093"})
    assert paused.status_code == 200
    assert paused.json()["status"] == "pending"
    queued = client.get("/api/admin/join-requests", headers=admin).json()
    assert any(row["id"] == paused.json()["id"] and row["status"] == "pending" for row in queued)
