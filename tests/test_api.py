import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add backend to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app
from app.config import settings
from app.database.session import Base, engine, SessionLocal
from app.models.project import Project
from app.schemas.llm import ContentPlanSchema

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture
def client():
    return TestClient(app)

def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "demo_mode" in data

def test_project_creation(client):
    payload = {
        "topic": "5 AI trends in 2026",
        "platform": "Qoneqt Global Feed",
        "duration": 30,
        "tone": "Educational"
    }
    response = client.post("/api/projects", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["topic"] == payload["topic"]
    assert data["platform"] == payload["platform"]
    assert data["status"] == "created"
    assert "id" in data

def test_project_status_and_get(client):
    # Create project
    create_res = client.post("/api/projects", json={"topic": "Test Status Pipeline", "duration": 20})
    project_id = create_res.json()["id"]

    # Status
    status_res = client.get(f"/api/projects/{project_id}/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["project_id"] == project_id
    assert status_data["status"] == "created"

    # Get details
    get_res = client.get(f"/api/projects/{project_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == project_id

def test_llm_schema_validation():
    sample_json = """{
        "title": "AI in 2026",
        "hook": "Is AI replacing you?",
        "summary": "Quick summary of AI",
        "script": "Full script here",
        "duration_seconds": 30,
        "scenes": [
            {
                "scene_number": 1,
                "duration": 6.0,
                "narration": "Intro narration",
                "visual_prompt": "Futuristic visual",
                "on_screen_text": "AI Revolution",
                "transition": "fade"
            }
        ],
        "caption": "Check this out!",
        "hashtags": ["#AI", "#Tech"]
    }"""
    parsed = ContentPlanSchema.model_validate_json(sample_json)
    assert parsed.title == "AI in 2026"
    assert len(parsed.scenes) == 1
    assert parsed.scenes[0].scene_number == 1
    assert parsed.scenes[0].duration == 6.0

def test_projects_list(client):
    response = client.get("/api/projects")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
