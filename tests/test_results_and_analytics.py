def test_rankings_empty_when_no_projects(client):
    r = client.get("/api/results/rankings")
    assert r.status_code == 200
    assert r.json()["rankings"] == []


def test_team_composition_reports_gaps(client):
    p1 = client.post("/api/participants/", json={
        "full_name": "A", "email": "a@x.com", "raw_skills_text": "react frontend"
    }).json()
    client.post(f"/api/skills/extract/{p1['id']}")

    team = client.post("/api/teams/", json={"name": "T", "member_ids": [p1["id"]]}).json()
    r = client.get(f"/api/teams/{team['id']}/composition")
    assert r.status_code == 200
    body = r.json()
    assert "coverage_gaps" in body
    assert "skill_diversity_score" in body
    assert body["skill_diversity_score"] >= 0


def test_analytics_overview_shape(client):
    r = client.get("/api/analytics/overview")
    assert r.status_code == 200
    body = r.json()
    for section in ["participants", "teams", "projects", "reviewers", "evaluations", "fairness"]:
        assert section in body


def test_project_for_unknown_team_404s(client):
    r = client.post("/api/projects/", json={"team_id": 9999, "title": "X", "description": "d"})
    assert r.status_code == 404


def test_reassign_no_show_replaces_reviewer(client):
    p1 = client.post("/api/participants/", json={"full_name": "A", "email": "a@x.com"}).json()
    team = client.post("/api/teams/", json={"name": "T", "member_ids": [p1["id"]]}).json()
    project = client.post("/api/projects/", json={"team_id": team["id"], "title": "P", "description": "d"}).json()

    rev1 = client.post("/api/reviewers/", json={"full_name": "R1", "email": "r1@x.com", "expertise_text": "python"}).json()
    rev2 = client.post("/api/reviewers/", json={"full_name": "R2", "email": "r2@x.com", "expertise_text": "python"}).json()

    client.post("/api/reviewers/assign", json={"reviewers_per_project": 1})
    assignments = client.get(f"/api/reviewers/assignments/{project['id']}").json()
    assigned_id = assignments[0]["reviewer_id"]

    r = client.post(f"/api/reviewers/reassign/{project['id']}/{assigned_id}")
    assert r.status_code == 200
    assert r.json()["new_reviewer_id"] != assigned_id
