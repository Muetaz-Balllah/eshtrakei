from datetime import timedelta

from fastapi.testclient import TestClient

from backend.db import SessionLocal
from backend.subscriptions.models import Subscription
from backend.utils import libya_today


def _login(client: TestClient, email: str, password: str) -> dict:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_pdf_notices_and_complaints(client: TestClient, caplog):
    joined = client.post("/api/join-requests", data={"name": "شركة الفاتورة", "description": "نت", "phone": "091"})
    admin = _login(client, "admin@eshtrakei.local", "phase0-admin-pass")
    company_id = client.post(f"/api/admin/join-requests/{joined.json()['id']}/approve", headers=admin).json()["id"]
    client.post(
        f"/api/admin/companies/{company_id}/manager",
        headers=admin,
        json={"full_name": "مدير", "email": "inv@eshtrakei.local", "password": "password1"},
    )
    manager = _login(client, "inv@eshtrakei.local", "password1")
    package_id = client.post(
        "/api/company/packages",
        headers=manager,
        json={"name": "شهر", "price": "40", "duration_amount": 30, "duration_unit": "days", "data_gb": 10, "speed_mbps": 8},
    ).json()["id"]
    buyer = client.post(
        "/api/auth/register",
        json={"full_name": "سالم", "city": "طرابلس", "phone": "092", "email": "salem@eshtrakei.local", "password": "password1"},
    )
    buyer_headers = {"Authorization": f"Bearer {buyer.json()['access_token']}"}
    bought = client.post(
        "/api/subscriptions/purchases",
        headers=buyer_headers,
        json={"company_id": company_id, "package_id": package_id, "idempotency_key": "pdf-key-0001", "simulated_outcome": "success"},
    )
    assert bought.status_code == 200
    invoice_id = bought.json()["invoice"]["id"]
    pdf = client.get(f"/api/invoices/{invoice_id}/pdf", headers=buyer_headers)
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")
    assert "salem@eshtrakei.local" in caplog.text
    assert client.get(f"/api/invoices/{invoice_id}/pdf", headers=admin).status_code == 403

    db = SessionLocal()
    row = db.get(Subscription, bought.json()["subscription"]["id"])
    row.end_date = libya_today() + timedelta(days=3)
    db.commit()
    other = db.get(Subscription, bought.json()["subscription"]["id"])
    db.close()
    assert other is not None
    assert client.post("/api/notifications/run-expiry-check", headers=admin).json()["created"] == 1
    assert client.post("/api/notifications/run-expiry-check", headers=admin).json()["created"] == 0
    notes = client.get("/api/notifications", headers=buyer_headers).json()
    assert "3" in notes[0]["message"]
    manager_notes = client.get("/api/notifications", headers=manager)
    assert manager_notes.status_code == 200
    assert any("ينتهي" in row["message"] for row in manager_notes.json())

    filed = client.post(
        "/api/complaints",
        headers=buyer_headers,
        json={"kind": "complaint", "target": "company", "company_id": company_id, "message": "انقطع النت"},
    )
    assert filed.status_code == 200
    complaint_id = filed.json()["id"]
    client.post(f"/api/company/complaints/{complaint_id}/reply", headers=manager, json={"message": "سنصلح الخط"})
    seen = client.get("/api/complaints", headers=buyer_headers).json()
    assert seen[0]["reply_message"] == "سنصلح الخط"
    platform = client.post(
        "/api/complaints",
        headers=buyer_headers,
        json={"kind": "technical_support", "target": "platform", "message": "الدخول بطيء"},
    )
    assert client.get("/api/company/complaints", headers=manager).json()[0]["id"] == complaint_id
    assert client.post(f"/api/admin/complaints/{platform.json()['id']}/reply", headers=admin, json={"message": "تم الاستلام"}).status_code == 200
    assert client.post(f"/api/company/complaints/{platform.json()['id']}/reply", headers=manager, json={"message": "لا"}).status_code == 404
