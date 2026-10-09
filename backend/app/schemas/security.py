from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class HashCalculationResponse(BaseModel):
    filename: str
    sha256_hash: str
    bytes_processed: int
    size_formatted: str
    status: str = "Hash calculated successfully."

class IntegrityVerifyResponse(BaseModel):
    filename: str
    calculated_hash: str
    reference_hash: str
    is_match: bool
    status: str
    bytes_processed: int
    details: str

class VideoMetadataSummary(BaseModel):
    filename: str
    file_size_bytes: int
    container_format: str
    duration_seconds: Optional[float] = None
    dimensions: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None
    creation_time: Optional[str] = None
    encoder: Optional[str] = None
    location: Optional[str] = None
    container_tags: Dict[str, Any] = {}
    stream_tags: Dict[str, Any] = {}
    chapters_count: int = 0
    raw_metadata: Optional[Dict[str, Any]] = None

class MetadataComparison(BaseModel):
    removed_fields: List[str]
    retained_fields: List[str]
    unverified_fields: List[str]
    details: List[Dict[str, Any]]

class MetadataSanitizeResponse(BaseModel):
    job_id: str
    original_filename: str
    sanitized_filename: str
    status: str
    download_url: str
    original: VideoMetadataSummary
    sanitized: VideoMetadataSummary
    comparison: MetadataComparison
    summary: str

class SecurityStatsResponse(BaseModel):
    authenticated: bool
    user_email: Optional[str] = None
    account_created_at: Optional[str] = None
    videos_checked_session: int = 0
    videos_sanitized_session: int = 0
