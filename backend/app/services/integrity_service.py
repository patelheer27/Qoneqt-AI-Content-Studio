import hashlib
import hmac
import re
from typing import Tuple, Dict, Any, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.config import settings
from app.models.security import SecurityLog

HEX_SHA256_REGEX = re.compile(r"^[a-fA-F0-9]{64}$")
CHUNK_SIZE = 64 * 1024 # 64 KB chunks

class IntegrityService:
    def format_size(self, size_bytes: int) -> str:
        """Formats byte count into human-readable string."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    async def calculate_hash(
        self,
        file: UploadFile,
        db: Optional[Session] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Incrementally streams file bytes in 64KB chunks to calculate SHA-256
        without loading the entire file into RAM. Enforces size limit.
        """
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        sha256 = hashlib.sha256()
        total_bytes = 0

        # Reset stream position if needed
        await file.seek(0)

        while True:
            chunk = await file.read(CHUNK_SIZE)
            if not chunk:
                break
            total_bytes += len(chunk)
            if total_bytes > max_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds permitted size of {settings.MAX_UPLOAD_SIZE_MB} MB."
                )
            sha256.update(chunk)

        calculated_hash = sha256.hexdigest()

        # Log activity if DB session provided
        if db:
            log = SecurityLog(
                user_id=user_id,
                event_type="integrity_calculated",
                details={
                    "filename": file.filename,
                    "sha256_hash": calculated_hash,
                    "bytes_processed": total_bytes
                }
            )
            db.add(log)
            db.commit()

        return {
            "filename": file.filename or "uploaded_video.mp4",
            "sha256_hash": calculated_hash,
            "bytes_processed": total_bytes,
            "size_formatted": self.format_size(total_bytes),
            "status": "Hash calculated successfully."
        }

    async def verify_integrity(
        self,
        file: UploadFile,
        reference_hash: str,
        db: Optional[Session] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validates reference hash format, computes actual SHA-256, and compares using hmac.compare_digest.
        """
        clean_ref = reference_hash.strip().lower()
        if not HEX_SHA256_REGEX.match(clean_ref):
            raise HTTPException(
                status_code=400,
                detail="Invalid reference hash. SHA-256 hash must be exactly 64 hexadecimal characters."
            )

        calc_result = await self.calculate_hash(file, db=None)
        actual_hash = calc_result["sha256_hash"]
        total_bytes = calc_result["bytes_processed"]

        # Constant-time comparison
        is_match = hmac.compare_digest(actual_hash.lower(), clean_ref)

        if is_match:
            status = "Integrity Verified — SHA-256 hashes match."
            details = "The calculated cryptographic hash of the uploaded file exactly matches the reference hash byte-for-byte."
        else:
            status = "Integrity Mismatch — SHA-256 hashes differ."
            details = "The calculated cryptographic hash differs from the reference hash. The file may have been modified, re-encoded, or corrupted."

        if db:
            log = SecurityLog(
                user_id=user_id,
                event_type="integrity_verified" if is_match else "integrity_mismatch",
                details={
                    "filename": file.filename,
                    "calculated_hash": actual_hash,
                    "reference_hash": clean_ref,
                    "is_match": is_match,
                    "bytes_processed": total_bytes
                }
            )
            db.add(log)
            db.commit()

        return {
            "filename": file.filename or "uploaded_video.mp4",
            "calculated_hash": actual_hash,
            "reference_hash": clean_ref,
            "is_match": is_match,
            "status": status,
            "bytes_processed": total_bytes,
            "details": details
        }

integrity_service = IntegrityService()
