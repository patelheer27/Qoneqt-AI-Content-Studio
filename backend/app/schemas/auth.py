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
    cooldown_seconds: int = 60
    expires_in_seconds: int = 300
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

    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    success: bool
    message: str
    session_token: str
    is_new_user: bool
    user: UserResponse

class SessionStatusResponse(BaseModel):
    authenticated: bool
    user: Optional[UserResponse] = None
    session_id: Optional[str] = None
