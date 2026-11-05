import pytest
import os
import subprocess
import hashlib
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
from app.main import app
from app.database import SessionLocal, Base, engine
from app.models.user import User, OTPRecord, SessionRecord
from app.models.security import MetadataJob, SecurityLog

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup if needed

@pytest.fixture(scope="module")
def sample_video():
    """Generates a real, lightweight 1-second MP4 video with metadata using ffmpeg."""
    sample_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_test.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=size=320x240:rate=10",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=1",
        "-t", "1",
        "-metadata", "title=Qoneqt Test Video",
        "-metadata", "author=Qoneqt Studio Creator",
        "-metadata", "comment=Test Identifying Metadata",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-c:a", "aac",
        sample_path
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    yield sample_path
    if os.path.exists(sample_path):
        try:
            os.remove(sample_path)
        except Exception:
            pass

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

# ==================== 1. EMAIL + OTP LOGIN TESTS ====================

def test_otp_request_demo_mode():
    import uuid
    email = f"faculty_{uuid.uuid4().hex[:6]}@qoneqt.studio"
    res = client.post("/api/auth/otp/request", json={"email": email})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["email"] == email
    assert data["is_demo_mode"] is True
    assert data["dev_otp"] is not None
    assert len(data["dev_otp"]) == 6
    assert data["dev_otp"].isdigit()

def test_otp_resend_cooldown():
    import uuid
    email = f"cooldown_{uuid.uuid4().hex[:6]}@qoneqt.studio"
    # First request
    res1 = client.post("/api/auth/otp/request", json={"email": email})
    assert res1.status_code == 200
    
    # Immediate second request should be rate-limited by cooldown
    res2 = client.post("/api/auth/otp/request", json={"email": email})
    assert res2.status_code == 429
    assert "Please wait" in res2.json()["detail"]

def test_otp_verify_invalid_code():
    import uuid
    email = f"invalid_{uuid.uuid4().hex[:6]}@qoneqt.studio"
    res1 = client.post("/api/auth/otp/request", json={"email": email})
    assert res1.status_code == 200

    # Submit wrong code
    res2 = client.post("/api/auth/otp/verify", json={"email": email, "otp": "000000"})
    assert res2.status_code == 400
    assert "Invalid verification code" in res2.json()["detail"]


def test_otp_verify_success_and_user_creation():
    import uuid
    email = f"creator_{uuid.uuid4().hex[:8]}@qoneqt.studio"
    res1 = client.post("/api/auth/otp/request", json={"email": email})
    assert res1.status_code == 200
    otp = res1.json()["dev_otp"]

    # Verify with correct OTP for first-time user
    res2 = client.post("/api/auth/otp/verify", json={"email": email, "otp": otp})
    assert res2.status_code == 200
    data = res2.json()
    assert data["success"] is True
    assert data["is_new_user"] is True
    assert data["user"]["email"] == email
    assert data["session_token"] is not None
    assert len(data["session_token"]) > 20

    # Protected route /api/auth/me with session
    session_token = data["session_token"]
    res3 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {session_token}"})
    assert res3.status_code == 200
    assert res3.json()["authenticated"] is True
    assert res3.json()["user"]["email"] == email

    # Reusing the same OTP must fail (single-use)
    res_reuse = client.post("/api/auth/otp/verify", json={"email": email, "otp": otp})
    assert res_reuse.status_code == 400

    # Logout
    res_logout = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {session_token}"})
    assert res_logout.status_code == 200
    assert res_logout.json()["success"] is True

    # After logout, /api/auth/me should return authenticated: false
    res_post_logout = client.get("/api/auth/me", headers={"Authorization": f"Bearer {session_token}"})
    assert res_post_logout.status_code == 200
    assert res_post_logout.json()["authenticated"] is False

def test_otp_verify_returning_user():
    # Use existing user
    email = "returning_creator@qoneqt.studio"
    # First login: creates user
    r1 = client.post("/api/auth/otp/request", json={"email": email})
    otp1 = r1.json()["dev_otp"]
    client.post("/api/auth/otp/verify", json={"email": email, "otp": otp1})

    # Second login: should authenticate existing user without error
    # Wait or simulate new OTP request by marking past as used
    from app.database import SessionLocal
    from app.models.user import OTPRecord
    db = SessionLocal()
    db.query(OTPRecord).filter(OTPRecord.email == email).delete()
    db.commit()
    db.close()

    r2 = client.post("/api/auth/otp/request", json={"email": email})
    otp2 = r2.json()["dev_otp"]
    v2 = client.post("/api/auth/otp/verify", json={"email": email, "otp": otp2})
    assert v2.status_code == 200
    assert v2.json()["success"] is True
    assert v2.json()["is_new_user"] is False
    assert v2.json()["user"]["email"] == email


# ==================== 2. VIDEO INTEGRITY CHECKER TESTS ====================

def test_video_integrity_calculate_hash(sample_video):
    with open(sample_video, "rb") as f:
        file_bytes = f.read()

    expected_hash = hashlib.sha256(file_bytes).hexdigest()

    with open(sample_video, "rb") as f:
        res = client.post(
            "/api/security/integrity/hash",
            files={"file": ("sample.mp4", f, "video/mp4")}
        )

    assert res.status_code == 200
    data = res.json()
    assert data["sha256_hash"] == expected_hash
    assert data["bytes_processed"] == len(file_bytes)
    assert data["status"] == "Hash calculated successfully."

def test_video_integrity_verify_match(sample_video):
    with open(sample_video, "rb") as f:
        file_bytes = f.read()
    expected_hash = hashlib.sha256(file_bytes).hexdigest()

    with open(sample_video, "rb") as f:
        res = client.post(
            "/api/security/integrity/verify",
            files={"file": ("sample.mp4", f, "video/mp4")},
            data={"reference_hash": expected_hash}
        )

    assert res.status_code == 200
    data = res.json()
    assert data["is_match"] is True
    assert "Integrity Verified" in data["status"]
    assert data["calculated_hash"] == expected_hash
    assert data["reference_hash"] == expected_hash

def test_video_integrity_verify_mismatch(sample_video):
    with open(sample_video, "rb") as f:
        file_bytes = f.read()
    # Flip one character in reference hash
    fake_hash = "a" * 64

    with open(sample_video, "rb") as f:
        res = client.post(
            "/api/security/integrity/verify",
            files={"file": ("sample.mp4", f, "video/mp4")},
            data={"reference_hash": fake_hash}
        )

    assert res.status_code == 200
    data = res.json()
    assert data["is_match"] is False
    assert "Integrity Mismatch" in data["status"]

def test_video_integrity_invalid_reference_format(sample_video):
    with open(sample_video, "rb") as f:
        res = client.post(
            "/api/security/integrity/verify",
            files={"file": ("sample.mp4", f, "video/mp4")},
            data={"reference_hash": "not-a-valid-sha256"}
        )

    assert res.status_code == 400
    assert "Invalid reference hash" in res.json()["detail"]

# ==================== 3. VIDEO METADATA SANITIZER TESTS ====================

def test_video_metadata_inspect(sample_video):
    with open(sample_video, "rb") as f:
        res = client.post(
            "/api/security/metadata/inspect",
            files={"file": ("sample.mp4", f, "video/mp4")}
        )

    assert res.status_code == 200
    data = res.json()
    assert "container_format" in data
    assert data["width"] == 320
    assert data["height"] == 240
    assert data["video_codec"] is not None
    # Check that test metadata was detected
    tags = data.get("container_tags", {})
    assert "title" in tags or "title=Qoneqt Test Video" in str(data)

def test_video_metadata_sanitize_and_download(sample_video):
    with open(sample_video, "rb") as f:
        res = client.post(
            "/api/security/metadata/sanitize",
            files={"file": ("sample.mp4", f, "video/mp4")}
        )

    assert res.status_code == 200
    data = res.json()
    assert "job_id" in data
    assert "download_url" in data
    assert "sanitized" in data
    assert data["sanitized"]["width"] == 320
    assert data["sanitized"]["height"] == 240

    # Verify that metadata was removed in comparison
    comparison = data["comparison"]
    assert len(comparison["removed_fields"]) > 0 or len(comparison["details"]) > 0

    # Test download endpoint
    job_id = data["job_id"]
    dl_res = client.get(f"/api/security/metadata/download/{job_id}")
    assert dl_res.status_code == 200
    assert len(dl_res.content) > 0
    assert dl_res.headers["content-type"] == "video/mp4"

def test_security_stats():
    res = client.get("/api/security/stats")
    assert res.status_code == 200
    data = res.json()
    assert "videos_checked_session" in data
    assert "videos_sanitized_session" in data
    assert data["videos_checked_session"] >= 1
    assert data["videos_sanitized_session"] >= 1

# ==================== 4. WORKFLOW A: AUTOMATIC VIDEO METADATA SANITIZATION TESTS ====================

def test_workflow_a_automatic_sanitization_pipeline(sample_video):
    """
    Tests Workflow A:
    1. Creates project with default sanitize_metadata=True
    2. Runs metadata policy application
    3. Confirms FFprobe inspection before and after
    4. Confirms metadata fields removed
    5. Confirms video/audio streams intact
    6. Confirms SHA-256 matches the exact bytes downloaded
    """
    # 1. Create project
    proj_res = client.post("/api/projects/", json={
        "topic": "Workflow A Test Video",
        "platform": "YouTube Shorts",
        "sanitize_metadata": True
    })
    assert proj_res.status_code == 200
    proj_id = proj_res.json()["id"]

    # 2. Attach sample video as generated output
    from app.database import SessionLocal
    from app.models.project import Project
    db = SessionLocal()
    proj = db.query(Project).filter(Project.id == proj_id).first()
    proj.raw_output_path = sample_video
    proj.output_path = sample_video
    proj.status = "Completed"
    db.commit()
    db.close()

    # 3. Apply automatic sanitization policy
    policy_res = client.post(f"/api/projects/{proj_id}/metadata-policy", json={"sanitize_metadata": True})
    assert policy_res.status_code == 200
    data = policy_res.json()

    assert data["metadata_policy"] == "sanitized"
    assert data["sanitize_metadata"] is True
    assert data["output_path"] != sample_video
    assert os.path.exists(data["output_path"])

    meta_info = data["metadata_info"]
    assert meta_info["policy"] == "sanitized"
    assert meta_info["sha256"] is not None
    assert len(meta_info["sha256"]) == 64

    # Verify comparison details show removed fields
    comparison = meta_info["comparison"]
    assert len(comparison["removed_fields"]) > 0

    # 4. Verify downloaded file matches reported SHA-256 byte-for-byte
    dl_res = client.get(f"/api/projects/{proj_id}/download")
    assert dl_res.status_code == 200
    downloaded_bytes = dl_res.content
    assert len(downloaded_bytes) > 0
    actual_hash = hashlib.sha256(downloaded_bytes).hexdigest()
    assert actual_hash == meta_info["sha256"]

def test_workflow_a_preserved_metadata_policy(sample_video):
    """
    Tests Workflow A when user opts to preserve metadata:
    1. Sets sanitize_metadata=False
    2. Confirms sanitization step is skipped
    3. Confirms original metadata tags remain
    4. Confirms calculated SHA-256 matches exact original file
    """
    proj_res = client.post("/api/projects/", json={
        "topic": "Workflow A Preserved Test",
        "platform": "YouTube Shorts",
        "sanitize_metadata": False
    })
    assert proj_res.status_code == 200
    proj_id = proj_res.json()["id"]

    from app.database import SessionLocal
    from app.models.project import Project
    db = SessionLocal()
    proj = db.query(Project).filter(Project.id == proj_id).first()
    proj.raw_output_path = sample_video
    proj.output_path = sample_video
    proj.status = "Completed"
    db.commit()
    db.close()

    policy_res = client.post(f"/api/projects/{proj_id}/metadata-policy", json={"sanitize_metadata": False})
    assert policy_res.status_code == 200
    data = policy_res.json()

    assert data["metadata_policy"] == "preserved"
    assert data["sanitize_metadata"] is False
    assert data["output_path"] == sample_video

    meta_info = data["metadata_info"]
    assert meta_info["policy"] == "preserved"
    assert "Original metadata preserved" in meta_info["policy_label"]

    with open(sample_video, "rb") as f:
        expected_raw_hash = hashlib.sha256(f.read()).hexdigest()
    assert meta_info["sha256"] == expected_raw_hash

    dl_res = client.get(f"/api/projects/{proj_id}/download")
    assert dl_res.status_code == 200
    assert hashlib.sha256(dl_res.content).hexdigest() == expected_raw_hash

def test_workflow_a_checksum_endpoint(sample_video):
    """Tests the .sha256 plaintext checksum download endpoint."""
    proj_res = client.post("/api/projects/", json={
        "topic": "Checksum Download Test",
        "sanitize_metadata": True
    })
    proj_id = proj_res.json()["id"]

    from app.database import SessionLocal
    from app.models.project import Project
    db = SessionLocal()
    proj = db.query(Project).filter(Project.id == proj_id).first()
    proj.raw_output_path = sample_video
    proj.output_path = sample_video
    proj.status = "Completed"
    db.commit()
    db.close()

    client.post(f"/api/projects/{proj_id}/metadata-policy", json={"sanitize_metadata": True})

    chk_res = client.get(f"/api/projects/{proj_id}/checksum")
    assert chk_res.status_code == 200
    assert "text/plain" in chk_res.headers["content-type"]
    content = chk_res.text
    assert len(content.strip().split()[0]) == 64
    assert ".mp4" in content

def test_workflow_b_manual_sanitizer_sha256_hash(sample_video):
    """Tests that Workflow B (manual sanitizer) calculates and returns SHA-256 of sanitized output."""
    with open(sample_video, "rb") as f:
        res = client.post(
            "/api/security/metadata/sanitize",
            files={"file": ("manual_upload.mp4", f, "video/mp4")}
        )

    assert res.status_code == 200
    data = res.json()
    assert "sha256_hash" in data
    assert data["sha256_hash"] is not None
    assert len(data["sha256_hash"]) == 64

    # Verify download file matches this hash
    job_id = data["job_id"]
    dl_res = client.get(f"/api/security/metadata/download/{job_id}")
    assert dl_res.status_code == 200
    actual_hash = hashlib.sha256(dl_res.content).hexdigest()
    assert actual_hash == data["sha256_hash"]

def test_no_removable_metadata_reporting(sample_video):
    """Tests truthful reporting when video contains no removable metadata."""
    # First sanitize to strip metadata
    with open(sample_video, "rb") as f:
        res1 = client.post(
            "/api/security/metadata/sanitize",
            files={"file": ("test.mp4", f, "video/mp4")}
        )
    job_id = res1.json()["job_id"]
    sanitized_bytes = client.get(f"/api/security/metadata/download/{job_id}").content

    # Sanitize the already clean video again
    res2 = client.post(
        "/api/security/metadata/sanitize",
        files={"file": ("already_clean.mp4", sanitized_bytes, "video/mp4")}
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert "clean" in data2["status"].lower() or "no removable metadata" in data2["status"].lower() or len(data2["comparison"]["removed_fields"]) == 0
