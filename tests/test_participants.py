def test_register_participant(client):
    r = client.post(
        "/api/participants/",
        json={"full_name": "Alice Kumar", "email": "alice@test.com", "organization": "VIT"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "alice@test.com"
    assert "id" in body


def test_duplicate_email_rejected(client):
    payload = {"full_name": "Alice Kumar", "email": "alice@test.com", "organization": "VIT"}
    r1 = client.post("/api/participants/", json=payload)
    assert r1.status_code == 201

    r2 = client.post("/api/participants/", json=payload)
    assert r2.status_code == 409


def test_fuzzy_name_duplicate_detected(client):
    client.post("/api/participants/", json={"full_name": "Alice Kumar", "email": "a1@test.com", "organization": "VIT"})
    r2 = client.post("/api/participants/", json={"full_name": "Alicia Kumar", "email": "a2@test.com", "organization": "VIT"})
    target_id = r2.json()["id"]

    r = client.post(f"/api/duplicates/check/{target_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["matches_found"] >= 1
    assert body["matches"][0]["match_type"] == "fuzzy_name"


def test_distinct_participants_not_flagged(client):
    client.post("/api/participants/", json={"full_name": "Bob Singh", "email": "bob@test.com", "organization": "MIT"})
    r2 = client.post("/api/participants/", json={"full_name": "Carla Diaz", "email": "carla@test.com", "organization": "Stanford"})
    target_id = r2.json()["id"]

    r = client.post(f"/api/duplicates/check/{target_id}")
    assert r.status_code == 200
    assert r.json()["matches_found"] == 0


def test_participant_not_found_404(client):
    r = client.get("/api/participants/9999")
    assert r.status_code == 404
