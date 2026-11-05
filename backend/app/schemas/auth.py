import re
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

class OTPRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(EMAIL_REGEX, clean):
            raise ValueError("Invalid email format")
        return clean

class OTPResponse(BaseModel):
    success: bool
    message: str
    email: str
    cooldown_seconds: int = 30
    expires_in_seconds: int = 60
    is_demo_mode: bool = False
    dev_otp: Optional[str] = None
    demo_note: Optional[str] = None

class OTPVerifyRequest(BaseModel):
    email: str
    otp: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(EMAIL_REGEX, clean):
            raise ValueError("Invalid email format")
        return clean

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        clean = v.strip()
        if not re.match(r"^\d{6}$", clean):
            raise ValueError("OTP must be exactly 6 digits")
        return clean

class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    last_login_at: datetime
    is_active: bool
    mfa_enabled: bool = False

    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    success: bool
    message: str
    session_token: Optional[str] = None
    is_new_user: bool = False
    mfa_required: bool = False
    mfa_token: Optional[str] = None
    user: Optional[UserResponse] = None

class SessionStatusResponse(BaseModel):
    authenticated: bool
    user: Optional[UserResponse] = None
    session_id: Optional[str] = None

# ==================== MFA SCHEMAS (Py_SecureVault Concept) ====================

class MFASetupResponse(BaseModel):
    secret: str
    qr_code: str
    issuer: str
    email: str

class MFAConfirmRequest(BaseModel):
    code: str

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        clean = v.replace(" ", "").strip()
        if not re.match(r"^\d{6}$", clean):
            raise ValueError("TOTP verification code must be exactly 6 digits.")
        return clean

class MFAConfirmResponse(BaseModel):
    success: bool
    message: str
    recovery_codes: list[str]

class MFAVerifyRequest(BaseModel):
    mfa_token: str
    code: str
    method: str = "totp" # 'totp' or 'recovery'

class MFAStatusResponse(BaseModel):
    mfa_enabled: bool
    recovery_codes_remaining: int
    is_locked: bool
    locked_until_minutes: int = 0

class MFADisableRequest(BaseModel):
    code: str
    method: str = "totp"

class MFARegenerateResponse(BaseModel):
    success: bool
    message: str
    recovery_codes: list[str]
