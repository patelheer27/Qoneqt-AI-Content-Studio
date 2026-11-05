import pytest
import time
import pyotp
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, Base, engine
from app.models.user import User
from app.services.mfa_service import mfa_service

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield

def test_mfa_full_lifecycle():
    """
    Tests complete MFA lifecycle based on Py_SecureVault concept:
    1. Register user & login Factor 1
    2. Initiate MFA setup (QR code & secret generation)
    3. Confirm enrollment with valid TOTP code
    4. Verify 8 recovery codes issued
    5. Test replay attack protection (reusing same code is blocked)
    6. Test Factor 1 -> Factor 2 login gate
    7. Test emergency recovery code usage (single-use validation)
    8. Test brute-force lockout after 5 failed attempts
    9. Test recovery code regeneration
    10. Test MFA disable
    """
    # 1. Create and authenticate user via Email OTP
    email = f"mfa_tester_{uuid.uuid4().hex[:6]}@qoneqt.studio"
    res_otp_req = client.post("/api/auth/otp/request", json={"email": email})
    assert res_otp_req.status_code == 200
    demo_otp = res_otp_req.json().get("dev_otp")
    assert demo_otp is not None

    res_verify = client.post("/api/auth/otp/verify", json={"email": email, "otp": demo_otp})
    assert res_verify.status_code == 200
    token = res_verify.json()["session_token"]
    assert token is not None
    assert res_verify.json()["mfa_required"] is False
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check initial MFA status
    res_status = client.get("/api/auth/mfa/status", headers=headers)
    assert res_status.status_code == 200
    assert res_status.json()["mfa_enabled"] is False

    # 3. Setup MFA
    res_setup = client.post("/api/auth/mfa/setup", headers=headers)
    assert res_setup.status_code == 200
    setup_data = res_setup.json()
    assert "secret" in setup_data
    assert "qr_code" in setup_data
    assert setup_data["qr_code"].startswith("data:image/png;base64,")

    # Get raw decrypted secret from DB to generate valid TOTP code
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    raw_secret = mfa_service.decrypt_secret(user.totp_secret_enc)
    db.close()
    assert raw_secret is not None

    # 4. Confirm enrollment with real TOTP code
    totp = pyotp.TOTP(raw_secret)
    valid_code = totp.now()

    res_confirm = client.post("/api/auth/mfa/confirm", json={"code": valid_code}, headers=headers)
    assert res_confirm.status_code == 200
    confirm_data = res_confirm.json()
    assert confirm_data["success"] is True
    recovery_codes = confirm_data["recovery_codes"]
    assert len(recovery_codes) == 8
    assert all("-" in code for code in recovery_codes)

    # 5. Verify status is now enabled with 8 codes
    res_status2 = client.get("/api/auth/mfa/status", headers=headers)
    assert res_status2.json()["mfa_enabled"] is True
    assert res_status2.json()["recovery_codes_remaining"] == 8

    # 6. Test Replay Attack Protection (Py_SecureVault Concept)
    # The same TOTP code within the same time-step MUST be rejected!
    res_replay = client.post("/api/auth/mfa/confirm", json={"code": valid_code}, headers=headers)
    assert res_replay.status_code == 400
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    replay_success, _, reason = mfa_service.verify_totp(raw_secret, valid_code, user.last_totp_step)
    db.close()
    assert replay_success is False
    assert "already used" in reason

    # 7. Test Login Flow with MFA Enforced
    from app.models.user import OTPRecord
    db = SessionLocal()
    # Mark old OTP as used or backdate created_at to bypass 60s resend cooldown in tests
    db.query(OTPRecord).filter(OTPRecord.email == email).delete()
    db.commit()
    db.close()

    res_otp_req2 = client.post("/api/auth/otp/request", json={"email": email})
    assert res_otp_req2.status_code == 200
    demo_otp2 = res_otp_req2.json()["dev_otp"]

    res_verify2 = client.post("/api/auth/otp/verify", json={"email": email, "otp": demo_otp2})
    assert res_verify2.status_code == 200
    v2_data = res_verify2.json()
    assert v2_data["mfa_required"] is True
    assert v2_data["session_token"] is None
    mfa_token = v2_data["mfa_token"]
    assert mfa_token is not None

    # 8. Test MFA Verification with Single-Use Recovery Code
    rec_code_to_use = recovery_codes[0]
    res_mfa_login = client.post("/api/auth/mfa/verify", json={
        "mfa_token": mfa_token,
        "code": rec_code_to_use,
        "method": "recovery"
    })
    assert res_mfa_login.status_code == 200
    mfa_login_data = res_mfa_login.json()
    assert mfa_login_data["success"] is True
    new_session_token = mfa_login_data["session_token"]
    assert new_session_token is not None
    new_headers = {"Authorization": f"Bearer {new_session_token}"}

    # Recovery codes remaining should now be 7
    res_status3 = client.get("/api/auth/mfa/status", headers=new_headers)
    assert res_status3.json()["recovery_codes_remaining"] == 7

    # 9. Test Recovery Code Burning (Cannot reuse the same recovery code)
    # Request a new login to test burned recovery code
    db = SessionLocal()
    db.query(OTPRecord).filter(OTPRecord.email == email).delete()
    db.commit()
    db.close()

    res_otp_req3 = client.post("/api/auth/otp/request", json={"email": email})
    assert res_otp_req3.status_code == 200
    res_verify3 = client.post("/api/auth/otp/verify", json={"email": email, "otp": res_otp_req3.json()["dev_otp"]})
    assert res_verify3.status_code == 200
    mfa_token2 = res_verify3.json()["mfa_token"]

    res_reused = client.post("/api/auth/mfa/verify", json={
        "mfa_token": mfa_token2,
        "code": rec_code_to_use,
        "method": "recovery"
    })
    assert res_reused.status_code == 400
    assert "Invalid or already-used" in res_reused.json()["detail"]

    # 10. Test Brute-Force Lockout (5 failed attempts locks for 5 minutes)
    for _ in range(4):
        client.post("/api/auth/mfa/verify", json={
            "mfa_token": mfa_token2,
            "code": "000000",
            "method": "totp"
        })
    res_locked = client.post("/api/auth/mfa/verify", json={
        "mfa_token": mfa_token2,
        "code": "000000",
        "method": "totp"
    })
    assert res_locked.status_code == 400
    assert "locked" in res_locked.json()["detail"].lower()

    # Reset lockout for remainder of test
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    mfa_service.reset_failures(db, user)
    db.close()

    # 11. Test Regenerate Recovery Codes
    res_regen = client.post("/api/auth/mfa/regenerate-recovery-codes", headers=new_headers)
    assert res_regen.status_code == 200
    new_recovery_codes = res_regen.json()["recovery_codes"]
    assert len(new_recovery_codes) == 8
    assert new_recovery_codes != recovery_codes

    res_status4 = client.get("/api/auth/mfa/status", headers=new_headers)
    assert res_status4.json()["recovery_codes_remaining"] == 8

    # 12. Test Disable MFA
    res_disable = client.post("/api/auth/mfa/disable", json={
        "code": new_recovery_codes[0],
        "method": "recovery"
    }, headers=new_headers)
    assert res_disable.status_code == 200
    assert res_disable.json()["success"] is True

    res_status5 = client.get("/api/auth/mfa/status", headers=new_headers)
    assert res_status5.json()["mfa_enabled"] is False
    assert res_status5.json()["recovery_codes_remaining"] == 0
