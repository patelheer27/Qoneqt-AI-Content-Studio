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
