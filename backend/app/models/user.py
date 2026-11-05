from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    last_login_at = Column(DateTime, default=utc_now)
    is_active = Column(Boolean, default=True)

    # Multi-Factor Authentication (MFA - RFC 6238 TOTP)
    totp_secret_enc = Column(String(512), nullable=True)  # Fernet encrypted TOTP secret
    mfa_enabled = Column(Boolean, default=False)
    last_totp_step = Column(Integer, nullable=True)        # Replay protection time-step
    failed_attempts = Column(Integer, default=0)           # Failed attempt counter for lockout
    locked_until = Column(DateTime, nullable=True)         # Lockout expiration timestamp

    sessions = relationship("SessionRecord", back_populates="user", cascade="all, delete-orphan")
    recovery_codes = relationship("RecoveryCode", back_populates="user", cascade="all, delete-orphan")

class RecoveryCode(Base):
    __tablename__ = "recovery_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash = Column(String(255), nullable=False) # Salted cryptographic hash of recovery code
    created_at = Column(DateTime, default=utc_now)
    used_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="recovery_codes")

class OTPRecord(Base):
    __tablename__ = "otp_records"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    otp_hash = Column(String(255), nullable=False) # Salted/HMAC hash of OTP
    created_at = Column(DateTime, default=utc_now)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    is_used = Column(Boolean, default=False)

class SessionRecord(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=utc_now)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)

    user = relationship("User", back_populates="sessions")
