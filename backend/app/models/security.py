from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Boolean
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
    event_type = Column(String(64), nullable=False, index=True) # integrity_verified, integrity_mismatch, metadata_inspected, metadata_sanitized, malware_scan_clean, malware_threat_detected, malware_unavailable
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utc_now)

class MalwareScanRecord(Base):
    __tablename__ = "malware_scans"

    scan_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False, index=True)
    status = Column(String(64), nullable=False) # Threat Detected, No Threat Detected, Scanner Unavailable, Scan Incomplete, Scan Failed, Invalid File, File Too Large
    threat_detected = Column(Boolean, nullable=True)
    threat_name = Column(String(255), nullable=True)
    engine = Column(String(128), default="ClamAV")
    engine_version = Column(String(128), nullable=True)
    message = Column(String(512), nullable=False)
    quarantine_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=utc_now)
