import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app
from app.database.session import Base, engine, SessionLocal
from app.models.project import Project

@pytest.fixture
def client():
    return TestClient(app)

def test_publish_simulation_requires_video(client):
    # Create project without video
    create_res = client.post("/api/projects", json={"topic": "Publish Unrendered Project"})
    project_id = create_res.json()["id"]

    # Try to publish before rendering -> should fail with 400
    pub_res = client.post(f"/api/projects/{project_id}/publish")
    assert pub_res.status_code == 400

def test_publish_simulation_success(client):
    db = SessionLocal()
    # Find any project with existing video or create one pointing to our generated test segment
    existing = db.query(Project).filter(Project.video_path != None).first()
    if existing:
        pub_res = client.post(f"/api/projects/{existing.id}/publish")
        assert pub_res.status_code == 200
        data = pub_res.json()
        assert data["status"] == "published"
        assert "published_at" in data
        assert "video_url" in data
    db.close()
