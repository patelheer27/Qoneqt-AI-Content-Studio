from fastapi import APIRouter, Depends, HTTPException, Header, Response, Cookie
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    OTPRequest, OTPResponse, OTPVerifyRequest,
    AuthResponse, UserResponse, SessionStatusResponse,
    MFASetupResponse, MFAConfirmRequest, MFAConfirmResponse,
    MFAVerifyRequest, MFAStatusResponse, MFADisableRequest,
    MFARegenerateResponse
)
from app.services.auth_service import auth_service
from app.services.mfa_service import mfa_service

router = APIRouter()

def get_session_token(
    authorization: Optional[str] = Header(None),
    qoneqt_session: Optional[str] = Cookie(None)
) -> Optional[str]:
    """Extract session token from Bearer header or HttpOnly cookie."""
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ", 1)[1].strip()
    if qoneqt_session:
        return qoneqt_session
    return None

def get_current_user(
    db: Session = Depends(get_db),
    session_token: Optional[str] = Depends(get_session_token)
) -> User:
    """Dependency that requires an authenticated user."""
    if not session_token:
        raise HTTPException(status_code=401, detail="Authentication required. Please log in.")
    user = auth_service.validate_session(db, session_token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid. Please log in again.")
    return user

def get_optional_user(
    db: Session = Depends(get_db),
    session_token: Optional[str] = Depends(get_session_token)
) -> Optional[User]:
    """Dependency for routes that work for both authenticated and guest users."""
    if not session_token:
        return None
    return auth_service.validate_session(db, session_token)

@router.post("/otp/request", response_model=OTPResponse)
def request_otp(req: OTPRequest, db: Session = Depends(get_db)):
    result = auth_service.request_otp(db, req.email)
    if not result.get("success"):
        raise HTTPException(status_code=429, detail=result.get("error"))
    return result

@router.post("/otp/resend", response_model=OTPResponse)
def resend_otp(req: OTPRequest, db: Session = Depends(get_db)):
    result = auth_service.request_otp(db, req.email)
    if not result.get("success"):
        raise HTTPException(status_code=429, detail=result.get("error"))
    return result

@router.post("/otp/verify", response_model=AuthResponse)
def verify_otp(
    req: OTPVerifyRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    res = auth_service.verify_otp(db, req.email, req.otp)
    success, message, user, session_token, is_new_user, mfa_required, mfa_token = res
    if not success or not user:
        raise HTTPException(status_code=400, detail=message)

    # If user has MFA enabled, return pending MFA state (Py_SecureVault Factor 2 gate)
    if mfa_required:
        return {
            "success": True,
            "message": message,
            "session_token": None,
            "is_new_user": is_new_user,
            "mfa_required": True,
            "mfa_token": mfa_token,
            "user": user
        }

    # Set secure cookie for browser session support
    response.set_cookie(
        key="qoneqt_session",
        value=session_token,
        httponly=True,
        samesite="lax",
        max_age=86400,
        secure=False # allows localhost HTTP development
    )

    return {
        "success": True,
        "message": message,
        "session_token": session_token,
        "is_new_user": is_new_user,
        "mfa_required": False,
        "mfa_token": None,
        "user": user
    }

# ==================== MFA ROUTES (Py_SecureVault Concept) ====================

@router.post("/mfa/verify", response_model=AuthResponse)
def verify_mfa_login(
    req: MFAVerifyRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Verifies Factor 2 (TOTP code or recovery code) during login.
    Enforces replay protection, clock drift, and account lockout.
    """
    success, message, user, session_token = mfa_service.verify_login_mfa(
        db, req.mfa_token, req.code, req.method
    )
    if not success or not user or not session_token:
        raise HTTPException(status_code=400, detail=message)

    # Set session cookie
    response.set_cookie(
        key="qoneqt_session",
        value=session_token,
        httponly=True,
        samesite="lax",
        max_age=86400,
        secure=False
    )

    return {
        "success": True,
        "message": message,
        "session_token": session_token,
        "is_new_user": False,
        "mfa_required": False,
        "mfa_token": None,
        "user": user
    }

@router.get("/mfa/status", response_model=MFAStatusResponse)
def get_mfa_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns current MFA enrollment status, remaining recovery codes, and lockout info."""
    remaining_recovery = mfa_service.count_remaining_recovery_codes(db, current_user.id)
    locked, mins = mfa_service.is_locked(current_user)
    return {
        "mfa_enabled": bool(current_user.mfa_enabled),
        "recovery_codes_remaining": remaining_recovery,
        "is_locked": locked,
        "locked_until_minutes": mins
    }

@router.post("/mfa/setup", response_model=MFASetupResponse)
def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generates encrypted TOTP secret, QR code, and manual key for authenticator apps."""
    setup_data = mfa_service.setup_mfa(db, current_user)
    return {
        "secret": setup_data["secret"],
        "qr_code": setup_data["qr_code"],
        "issuer": setup_data["issuer"],
        "email": setup_data["email"]
    }

@router.post("/mfa/confirm", response_model=MFAConfirmResponse)
def confirm_mfa(
    req: MFAConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirms setup with a 6-digit TOTP code from user's authenticator app.
    Enables MFA and issues 8 single-use recovery codes.
    """
    success, message, recovery_codes = mfa_service.confirm_mfa_setup(
        db, current_user, req.code
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {
        "success": True,
        "message": message,
        "recovery_codes": recovery_codes
    }

@router.post("/mfa/regenerate-recovery-codes", response_model=MFARegenerateResponse)
def regenerate_recovery_codes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invalidates old recovery codes and generates 8 new single-use recovery codes."""
    if not current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA must be active to regenerate recovery codes.")

    new_codes = mfa_service.generate_recovery_codes(db, current_user.id)
    return {
        "success": True,
        "message": "New recovery codes generated. All previous codes have been invalidated.",
        "recovery_codes": new_codes
    }

@router.post("/mfa/disable")
def disable_mfa(
    req: MFADisableRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disables MFA after validating current TOTP code or recovery code."""
    success, message = mfa_service.disable_mfa(db, current_user, req.code, req.method)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}

@router.get("/me", response_model=SessionStatusResponse)
def get_current_session(
    current_user: Optional[User] = Depends(get_optional_user),
    session_token: Optional[str] = Depends(get_session_token)
):
    if not current_user:
        return {
            "authenticated": False,
            "user": None,
            "session_id": None
        }
    return {
        "authenticated": True,
        "user": current_user,
        "session_id": session_token[:8] + "..." if session_token else None
    }

@router.post("/logout")
def logout(
    response: Response,
    db: Session = Depends(get_db),
    session_token: Optional[str] = Depends(get_session_token)
):
    if session_token:
        auth_service.logout_session(db, session_token)
    response.delete_cookie("qoneqt_session")
    return {"success": True, "message": "Successfully logged out."}
