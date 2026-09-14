from tests.conftest import auth_header


def test_personas(client):
    r = client.get("/auth/personas")
    assert r.status_code == 200
    emails = {p["email"] for p in r.json()}
    assert "patient@demo.matchcare.local" in emails
    assert "admin@summit.matchcare.local" in emails


def test_login_and_me(client):
    headers = auth_header(client, "patient@demo.matchcare.local")
    me = client.get("/auth/me", headers=headers)
    assert me.status_code == 200
    body = me.json()
    assert body["role"] == "patient"
    assert body["organization"]["slug"] == "bayview"
    assert body["patient"]["access_tier"] == "premium"


def test_bad_login(client):
    r = client.post("/auth/token", json={"email": "patient@demo.matchcare.local", "password": "wrong"})
    assert r.status_code == 401


def test_match_ranked_with_breakdown(client):
    headers = auth_header(client, "patient@demo.matchcare.local")
    r = client.post("/match", headers=headers, json={"require_tier": True, "limit": 10})
    assert r.status_code == 200, r.text
    body = r.json()
    assert "formula" in body
    assert len(body["results"]) >= 1
    top = body["results"][0]
    assert 0 <= top["score"] <= 1
    bd = top["breakdown"]
    for key in ("specialty", "location", "tier", "availability", "weights"):
        assert key in bd
    # scores should be non-increasing
    scores = [row["score"] for row in body["results"]]
    assert scores == sorted(scores, reverse=True)
    # cardiology specialist in SF should rank well for Ava
    names = [row["provider"]["display_name"] for row in body["results"]]
    assert any("Okonkwo" in n or "Feldman" in n or "Nair" in n for n in names[:5])


def test_match_requires_patient_role(client):
    headers = auth_header(client, "provider@demo.matchcare.local")
    r = client.post("/match", headers=headers, json={})
    assert r.status_code == 403


def test_tenant_isolation_on_providers(client):
    bay = auth_header(client, "patient@demo.matchcare.local")
    summit = auth_header(client, "patient@summit.matchcare.local")
    bay_providers = client.get("/providers", headers=bay).json()
    summit_providers = client.get("/providers", headers=summit).json()
    bay_ids = {p["user_id"] for p in bay_providers}
    summit_ids = {p["user_id"] for p in summit_providers}
    assert bay_ids.isdisjoint(summit_ids)
    assert any(p["city"] == "San Francisco" for p in bay_providers)
    assert any(p["city"] == "Denver" for p in summit_providers)
