import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # SQLite default with robust absolute path
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'video_studio.db').replace(os.sep, '/')}"
    )
    
    DEMO_MODE: str = "false"
    POLLINATIONS_API_KEY: str = os.getenv("POLLINATIONS_API_KEY", "")

    # Security & Authentication Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "qoneqt-ai-content-studio-super-secret-key-2026")
    SESSION_TTL_HOURS: int = int(os.getenv("SESSION_TTL_HOURS", "24"))
    
    # OTP Configuration (Expires within 1 minute / 60 seconds)
    OTP_TTL_SECONDS: int = int(os.getenv("OTP_TTL_SECONDS", "60"))
    OTP_RESEND_COOLDOWN_SECONDS: int = int(os.getenv("OTP_RESEND_COOLDOWN_SECONDS", "30"))
    OTP_MAX_ATTEMPTS: int = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))
    OTP_DEMO_MODE: bool = os.getenv("OTP_DEMO_MODE", "true").lower() in ("true", "1", "yes")

    # SMTP Email Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "noreply@qoneqt.studio")

    # Media Integrity & Sanitization limits
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
    FFMPEG_TIMEOUT_SECONDS: int = int(os.getenv("FFMPEG_TIMEOUT_SECONDS", "120"))
    METADATA_RETENTION_HOURS: int = int(os.getenv("METADATA_RETENTION_HOURS", "24"))

    # Multi-Factor Authentication (MFA - RFC 6238 TOTP) Configuration
    TOTP_ISSUER: str = os.getenv("TOTP_ISSUER", "Qoneqt AI Studio")
    MFA_LOCKOUT_MINUTES: int = int(os.getenv("MFA_LOCKOUT_MINUTES", "5"))
    MFA_MAX_FAILED_ATTEMPTS: int = int(os.getenv("MFA_MAX_FAILED_ATTEMPTS", "5"))
    MFA_PENDING_TTL_SECONDS: int = int(os.getenv("MFA_PENDING_TTL_SECONDS", "300"))
    TOTP_ENCRYPTION_KEY: Optional[str] = os.getenv("TOTP_ENCRYPTION_KEY", None)

    # Malware Scanner (ClamAV) Configuration
    CLAMAV_ENABLED: bool = os.getenv("CLAMAV_ENABLED", "true").lower() in ("true", "1", "yes")
    CLAMAV_HOST: str = os.getenv("CLAMAV_HOST", "127.0.0.1")
    CLAMAV_PORT: int = int(os.getenv("CLAMAV_PORT", "3310"))
    CLAMAV_SOCKET_PATH: Optional[str] = os.getenv("CLAMAV_SOCKET_PATH", None)
    MAX_SCAN_FILE_SIZE_MB: int = int(os.getenv("MAX_SCAN_FILE_SIZE_MB", "100"))
    SCAN_TIMEOUT_SECONDS: int = int(os.getenv("SCAN_TIMEOUT_SECONDS", "30"))
    QUARANTINE_DIR: str = os.getenv("QUARANTINE_DIR", "quarantine")
    MALWARE_SCAN_ENFORCED: bool = os.getenv("MALWARE_SCAN_ENFORCED", "false").lower() in ("true", "1", "yes")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

