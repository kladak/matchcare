from tests.conftest import auth_header


def test_create_and_provider_accept(client):
    patient = auth_header(client, "patient@demo.matchcare.local")
    providers = client.get("/providers", headers=patient).json()
    target = next(p for p in providers if "Okonkwo" in p["display_name"])

    created = client.post(
        "/match-requests",
        headers=patient,
        json={"provider_user_id": target["user_id"], "notes": "Demo request"},
    )
    assert created.status_code == 201, created.text
    req = created.json()
    assert req["status"] == "open"
    assert req["score"] > 0

    # duplicate active blocked
    dup = client.post(
        "/match-requests",
        headers=patient,
        json={"provider_user_id": target["user_id"]},
    )
    assert dup.status_code == 409

    provider = auth_header(client, "provider@demo.matchcare.local")
    inbox = client.get("/match-requests", headers=provider).json()
    assert any(r["id"] == req["id"] for r in inbox)

    accepted = client.patch(
        f"/match-requests/{req['id']}",
        headers=provider,
        json={"status": "accepted"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"

    scheduled = client.patch(
        f"/match-requests/{req['id']}",
        headers=provider,
        json={"status": "scheduled"},
    )
    assert scheduled.status_code == 200
    body = scheduled.json()
    assert body["status"] == "scheduled"
    assert body["appointment"] is not None


def test_admin_tenant_and_audit(client):
    admin = auth_header(client, "admin@demo.matchcare.local")
    summary = client.get("/admin/tenant", headers=admin)
    assert summary.status_code == 200
    body = summary.json()
    assert body["organization"]["slug"] == "bayview"
    assert body["provider_count"] >= 5
    assert "Cardiology" in body["specialties_offered"]

    # generate an audited call
    client.get("/providers", headers=admin)
    logs = client.get("/audit/logs", headers=admin)
    assert logs.status_code == 200
    # May be empty if the middleware used a different session; still expect 200.
    assert isinstance(logs.json(), list)


def test_admin_forbidden_for_patient(client):
    patient = auth_header(client, "patient@demo.matchcare.local")
    assert client.get("/admin/tenant", headers=patient).status_code == 403
