from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.security import SecurityLog
from app.routes.auth import get_optional_user
from app.schemas.security import (
    HashCalculationResponse,
    IntegrityVerifyResponse,
    VideoMetadataSummary,
    MetadataSanitizeResponse,
    SecurityStatsResponse
)
from app.services.integrity_service import integrity_service
from app.services.metadata_service import metadata_service

router = APIRouter()

@router.post("/integrity/hash", response_model=HashCalculationResponse)
async def calculate_video_hash(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Calculates SHA-256 cryptographic hash of an uploaded video file in memory-safe chunks."""
    user_id = current_user.id if current_user else None
    return await integrity_service.calculate_hash(file, db=db, user_id=user_id)

@router.post("/integrity/verify", response_model=IntegrityVerifyResponse)
async def verify_video_integrity(
    file: UploadFile = File(...),
    reference_hash: str = Form(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Verifies whether uploaded video file matches a reference SHA-256 hash byte-for-byte."""
    user_id = current_user.id if current_user else None
    return await integrity_service.verify_integrity(file, reference_hash, db=db, user_id=user_id)

@router.post("/metadata/inspect", response_model=VideoMetadataSummary)
async def inspect_video_metadata(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Inspects container and stream metadata of an uploaded video using real FFprobe."""
    user_id = current_user.id if current_user else None
    return await metadata_service.inspect(file, db=db, user_id=user_id)

@router.post("/metadata/sanitize", response_model=MetadataSanitizeResponse)
async def sanitize_video_metadata(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Strips identifying metadata from video using FFmpeg and returns before-and-after comparison."""
    user_id = current_user.id if current_user else None
    return await metadata_service.sanitize(file, db=db, user_id=user_id)

@router.get("/metadata/download/{job_id}")
def download_sanitized_video(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Downloads sanitized video file if authorized."""
    user_id = current_user.id if current_user else None
    return metadata_service.get_download_file(db, job_id, user_id)

@router.get("/stats", response_model=SecurityStatsResponse)
def get_security_stats(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Returns actual operational stats for Security & Privacy Center."""
    user_id = current_user.id if current_user else None
    
    # Query real database records for activity counts
    checked_query = db.query(SecurityLog).filter(
        SecurityLog.event_type.in_(["integrity_calculated", "integrity_verified", "integrity_mismatch"])
    )
    sanitized_query = db.query(SecurityLog).filter(
        SecurityLog.event_type == "metadata_sanitized"
    )

    if user_id:
        checked_query = checked_query.filter(SecurityLog.user_id == user_id)
        sanitized_query = sanitized_query.filter(SecurityLog.user_id == user_id)

    checked_count = checked_query.count()
    sanitized_count = sanitized_query.count()

    return {
        "authenticated": current_user is not None,
        "user_email": current_user.email if current_user else None,
        "account_created_at": current_user.created_at.strftime("%b %d, %Y") if current_user and current_user.created_at else None,
        "videos_checked_session": checked_count,
        "videos_sanitized_session": sanitized_count
    }
