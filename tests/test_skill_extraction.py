from app.utils.gemini_client import extract_skills, _fallback_extract


def test_fallback_extract_finds_known_tags():
    tags = _fallback_extract("I love react, python, and devops with aws")
    assert "react" in tags
    assert "python" in tags
    assert "devops" in tags
    assert "cloud" in tags


def test_fallback_extract_empty_text():
    assert _fallback_extract("") == []


def test_extract_skills_uses_fallback_without_api_key():
    # conftest forces GEMINI_API_KEY="" so this exercises the no-network path
    result = extract_skills("machine learning and react expert")
    assert "machine-learning" in result
    assert "react" in result


def test_extract_skills_handles_empty_input():
    assert extract_skills("") == []
    assert extract_skills("   ") == []


def test_skill_extract_preview_endpoint(client):
    r = client.post("/api/skills/extract", json={"raw_text": "backend developer with sql and java"})
    assert r.status_code == 200
    skills = r.json()["normalized_skills"]
    assert "backend" in skills
    assert "sql" in skills
    assert "java" in skills
