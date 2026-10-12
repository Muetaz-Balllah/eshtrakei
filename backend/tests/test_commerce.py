from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient


def _login(client: TestClient, email: str, password: str) -> dict:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _company(client: TestClient, name: str, manager_email: str) -> tuple[dict, int]:
    joined = client.post("/api/join-requests", data={"name": name, "description": "نت", "phone": "091"})
    admin = _login(client, "admin@eshtrakei.local", "phase0-admin-pass")
    request_id = joined.json()["id"]
    company_id = client.post(f"/api/admin/join-requests/{request_id}/approve", headers=admin).json()["id"]
    client.post(
        f"/api/admin/companies/{company_id}/manager",
        headers=admin,
        json={"full_name": "موظف", "email": manager_email, "password": "password1"},
    )
    return _login(client, manager_email, "password1"), company_id


def test_packages_coupons_purchase_and_renewal(client: TestClient):
    manager, company_id = _company(client, "شركة السرعة", "speed@eshtrakei.local")
    other, _other_id = _company(client, "شركة أخرى", "otherco@eshtrakei.local")
    created = client.post(
        "/api/company/packages",
        headers=manager,
        json={"name": "باقة شهر", "price": "100.00", "duration_amount": 1, "duration_unit": "months", "data_gb": 50, "speed_mbps": 20},
    )
    assert created.status_code == 200, created.text
    package_id = created.json()["id"]
    assert created.json()["currency"] == "LYD"
    assert client.patch(f"/api/company/packages/{package_id}", headers=other, json=created.json()).status_code == 404

    buyer = client.post(
        "/api/auth/register",
        json={"full_name": "مشتري", "city": "طرابلس", "phone": "091000", "email": "buyer@eshtrakei.local", "password": "password1"},
    )
    buyer_headers = {"Authorization": f"Bearer {buyer.json()['access_token']}"}
    visible = client.get(f"/api/companies/{company_id}/packages", headers=buyer_headers)
    assert visible.json()[0]["data_gb"] == 50

    expires = (datetime.now(UTC) + timedelta(days=3)).isoformat()
    coupon = client.post(
        "/api/company/coupons",
        headers=manager,
        json={"code": "save", "discount_amount": "15.00", "expires_at": expires},
    )
    assert coupon.status_code == 200
    card = client.post(
        "/api/subscriptions/purchases",
        headers=buyer_headers,
        json={"company_id": company_id, "package_id": package_id, "idempotency_key": "card-key-001", "simulated_outcome": "success", "card_number": "4242"},
    )
    assert card.status_code == 422

    failed = client.post(
        "/api/subscriptions/purchases",
        headers=buyer_headers,
        json={"company_id": company_id, "package_id": package_id, "idempotency_key": "fail-key-001", "simulated_outcome": "failure", "coupon_code": "SAVE"},
    )
    assert failed.json()["payment_status"] == "failed"
    assert client.get("/api/subscriptions", headers=buyer_headers).json() == []

    bought = client.post(
        "/api/subscriptions/purchases",
        headers=buyer_headers,
        json={"company_id": company_id, "package_id": package_id, "idempotency_key": "ok-key-00001", "simulated_outcome": "success", "coupon_code": "SAVE"},
    )
    assert bought.status_code == 200, bought.text
    assert bought.json()["invoice"]["amount_paid"] == "85.00"
    assert bought.json()["invoice"]["currency"] == "LYD"
    subscription_id = bought.json()["subscription"]["id"]
    again = client.post(
        "/api/subscriptions/purchases",
        headers=buyer_headers,
        json={"company_id": company_id, "package_id": package_id, "idempotency_key": "ok-key-00002", "simulated_outcome": "success"},
    )
    assert again.status_code == 409
    reused = client.post(
        "/api/subscriptions/purchases",
        headers=buyer_headers,
        json={"company_id": company_id, "package_id": package_id, "idempotency_key": "ok-key-00001", "simulated_outcome": "success", "coupon_code": "SAVE"},
    )
    assert reused.json()["subscription"]["id"] == subscription_id

    renewed = client.post(
        f"/api/subscriptions/{subscription_id}/renew",
        headers=buyer_headers,
        json={"idempotency_key": "renew-key-001", "simulated_outcome": "success", "coupon_code": "SAVE"},
    )
    assert renewed.status_code == 422
    renewed = client.post(
        f"/api/subscriptions/{subscription_id}/renew",
        headers=buyer_headers,
        json={"idempotency_key": "renew-key-001", "simulated_outcome": "success"},
    )
    assert renewed.status_code == 200, renewed.text
    assert renewed.json()["subscription"]["id"] != subscription_id
    assert renewed.json()["invoice"]["invoice_number"] != bought.json()["invoice"]["invoice_number"]

    hidden = client.post(f"/api/company/packages/{package_id}/stop", headers=manager)
    assert hidden.json()["is_available"] is False
    assert client.get(f"/api/companies/{company_id}/packages", headers=buyer_headers).json() == []
    clients = client.get("/api/company/clients", headers=manager)
    assert clients.json()[0]["email"] == "buyer@eshtrakei.local"
    assert client.get("/api/company/clients", headers=other).json() == []


def test_coupon_larger_than_subscription_charges_nothing(client: TestClient):
    manager, company_id = _company(client, "شركة الخصم", "discount@eshtrakei.local")
    created = client.post(
        "/api/company/packages",
        headers=manager,
        json={"name": "باقة صغيرة", "price": "40.00", "duration_amount": 7, "duration_unit": "days", "data_gb": 10, "speed_mbps": 8},
    )
    package_id = created.json()["id"]
    expires = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    coupon = client.post(
        "/api/company/coupons",
        headers=manager,
        json={"code": "big", "discount_amount": "100.00", "expires_at": expires},
    )
    assert coupon.status_code == 200, coupon.text

    buyer = client.post(
        "/api/auth/register",
        json={"full_name": "زبون الخصم", "city": "طرابلس", "phone": "091111", "email": "discount-buyer@eshtrakei.local", "password": "password1"},
    )
    headers = {"Authorization": f"Bearer {buyer.json()['access_token']}"}
    topped = client.post("/api/wallet/topups", headers=headers, json={"amount": "12.00", "simulated_outcome": "success"})
    assert topped.status_code == 200, topped.text

    bought = client.post(
        "/api/subscriptions/purchases",
        headers=headers,
        json={"company_id": company_id, "package_id": package_id, "coupon_code": "  big  ", "idempotency_key": "big-coupon-0001", "pay_with_wallet": True},
    )
    assert bought.status_code == 200, bought.text
    assert bought.json()["payment_status"] == "succeeded"
    assert bought.json()["invoice"]["amount_paid"] == "0.00"
    wallet = client.get("/api/wallet", headers=headers)
    assert wallet.json()["balance"] == "12.00"

    reused = client.post(
        "/api/subscriptions/purchases",
        headers=headers,
        json={"company_id": company_id, "package_id": package_id, "coupon_code": "BIG", "idempotency_key": "big-coupon-0002", "pay_with_wallet": True},
    )
    assert reused.status_code == 409
