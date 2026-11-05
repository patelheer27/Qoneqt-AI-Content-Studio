from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.security import SecurityLog, MalwareScanRecord
from app.routes.auth import get_optional_user
from app.schemas.security import (
    HashCalculationResponse,
    IntegrityVerifyResponse,
    VideoMetadataSummary,
    MetadataSanitizeResponse,
    SecurityStatsResponse,
    MalwareStatusResponse,
    MalwareScanResponse,
    MalwareHistoryResponse
)
from app.services.integrity_service import integrity_service
from app.services.metadata_service import metadata_service
from app.services.malware_service import malware_scanner_service
from app.config import settings

router = APIRouter()

# ==================== FEATURE 2: VIDEO INTEGRITY CHECKER ====================

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

# ==================== FEATURE 3: VIDEO METADATA SANITIZER ====================

@router.post("/metadata/inspect", response_model=VideoMetadataSummary)
async def inspect_video_metadata(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Inspects container and stream metadata of an uploaded video using real FFprobe."""
    user_id = current_user.id if current_user else None

    # Check for malware if scanner is active or enforced
    status = malware_scanner_service.get_status()
    if status.get("available"):
        scan_res = await malware_scanner_service.scan_upload(file, db=db, user_id=user_id)
        if scan_res.get("threat_detected"):
            raise HTTPException(
                status_code=400,
                detail=f"Malware threat detected in uploaded video: {scan_res.get('threat_name')}. Processing blocked."
            )
        await file.seek(0)
    elif settings.MALWARE_SCAN_ENFORCED:
        raise HTTPException(
            status_code=503,
            detail="Malware scanning is mandatory before processing, but the antivirus engine is currently unavailable."
        )

    return await metadata_service.inspect(file, db=db, user_id=user_id)

@router.post("/metadata/sanitize", response_model=MetadataSanitizeResponse)
async def sanitize_video_metadata(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Strips identifying metadata from video using FFmpeg and returns before-and-after comparison."""
    user_id = current_user.id if current_user else None

    # Check for malware if scanner is active or enforced
    status = malware_scanner_service.get_status()
    if status.get("available"):
        scan_res = await malware_scanner_service.scan_upload(file, db=db, user_id=user_id)
        if scan_res.get("threat_detected"):
            raise HTTPException(
                status_code=400,
                detail=f"Malware threat detected in uploaded video: {scan_res.get('threat_name')}. Processing blocked."
            )
        await file.seek(0)
    elif settings.MALWARE_SCAN_ENFORCED:
        raise HTTPException(
            status_code=503,
            detail="Malware scanning is mandatory before processing, but the antivirus engine is currently unavailable."
        )

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

# ==================== FEATURE 4: MALWARE SCANNER (CLAMAV) ====================

@router.get("/malware/status", response_model=MalwareStatusResponse)
def get_malware_scanner_status():
    """Inspects ClamAV availability, network daemon or CLI binary, returning live status."""
    return malware_scanner_service.get_status()

@router.post("/malware/scan", response_model=MalwareScanResponse)
async def scan_file_for_malware(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Uploads a file to a secure sandbox, validates file size and extension,
    computes SHA-256 hash incrementally, submits to ClamAV, and quarantines threats.
    """
    user_id = current_user.id if current_user else None
    return await malware_scanner_service.scan_upload(file, db=db, user_id=user_id)

@router.get("/malware/scans/{scan_id}", response_model=MalwareScanResponse)
def get_malware_scan_report(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Retrieves an authorized scan report by scan_id."""
    user_id = current_user.id if current_user else None
    report = malware_scanner_service.get_scan_by_id(db, scan_id, user_id=user_id)
    if not report:
        raise HTTPException(status_code=404, detail="Scan record not found or access unauthorized.")
    return report

@router.get("/malware/history", response_model=MalwareHistoryResponse)
def get_malware_scan_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Retrieves recent scan records for the current user or session."""
    user_id = current_user.id if current_user else None
    return malware_scanner_service.get_history(db, user_id=user_id, limit=limit)

@router.get("/quarantine/{scan_id}")
def download_quarantined_file():
    """Explicitly blocks downloading quarantined files for security."""
    raise HTTPException(
        status_code=403,
        detail="Access denied: Quarantined files are restricted and cannot be downloaded or processed."
    )

# ==================== OVERALL SECURITY STATS ====================

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
    scan_query = db.query(MalwareScanRecord)
    threat_query = db.query(MalwareScanRecord).filter(MalwareScanRecord.threat_detected == True)

    if user_id:
        checked_query = checked_query.filter(SecurityLog.user_id == user_id)
        sanitized_query = sanitized_query.filter(SecurityLog.user_id == user_id)
        scan_query = scan_query.filter(MalwareScanRecord.user_id == user_id)
        threat_query = threat_query.filter(MalwareScanRecord.user_id == user_id)

    checked_count = checked_query.count()
    sanitized_count = sanitized_query.count()
    scanned_count = scan_query.count()
    threats_count = threat_query.count()

    return {
        "authenticated": current_user is not None,
        "user_email": current_user.email if current_user else None,
        "account_created_at": current_user.created_at.strftime("%b %d, %Y") if current_user and current_user.created_at else None,
        "videos_checked_session": checked_count,
        "videos_sanitized_session": sanitized_count,
        "scans_performed_session": scanned_count,
        "threats_blocked_session": threats_count
    }

