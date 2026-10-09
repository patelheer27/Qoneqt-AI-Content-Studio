from fastapi import APIRouter, Depends, HTTPException, Header, Response, Cookie
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    OTPRequest, OTPResponse, OTPVerifyRequest,
    AuthResponse, UserResponse, SessionStatusResponse
)
from app.services.auth_service import auth_service

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
    success, message, user, session_token, is_new_user = auth_service.verify_otp(
        db, req.email, req.otp
    )
    if not success or not user or not session_token:
        raise HTTPException(status_code=400, detail=message)

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
        "user": user
    }

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
