from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from datetime import datetime, timezone
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class MetadataJob(Base):
    __tablename__ = "metadata_jobs"

    job_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    original_filename = Column(String(255), nullable=False)
    sanitized_filename = Column(String(255), nullable=False)
    sanitized_path = Column(String(512), nullable=False)
    original_metadata = Column(JSON, nullable=True)
    sanitized_metadata = Column(JSON, nullable=True)
    comparison = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    expires_at = Column(DateTime, nullable=True)

class SecurityLog(Base):
    __tablename__ = "security_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    event_type = Column(String(64), nullable=False, index=True) # integrity_verified, integrity_mismatch, metadata_inspected, metadata_sanitized
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now)
