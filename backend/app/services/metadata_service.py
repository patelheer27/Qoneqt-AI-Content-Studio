import os
import json
import uuid
import shutil
import subprocess
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.config import settings
from app.models.security import MetadataJob, SecurityLog

def utc_now():
    return datetime.now(timezone.utc)

class MetadataService:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.storage_dir = os.path.join(base_dir, "storage")
        self.temp_dir = os.path.join(self.storage_dir, "temp")
        self.sanitized_dir = os.path.join(self.storage_dir, "renders", "sanitized")
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.sanitized_dir, exist_ok=True)

    def _find_ffprobe_cmd(self) -> str:
        """Finds ffprobe executable in PATH or standard Python Scripts directory."""
        if shutil.which("ffprobe"):
            return "ffprobe"
        candidates = [
            r"C:\Users\Dell\AppData\Local\Programs\Python\Python314\Scripts\ffprobe.exe",
            r"C:\Program Files\ffmpeg\bin\ffprobe.exe"
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return "ffprobe"

    def _find_ffmpeg_cmd(self) -> str:
        """Finds ffmpeg executable in PATH or standard directory."""
        if shutil.which("ffmpeg"):
            return "ffmpeg"
        candidates = [
            r"C:\Users\Dell\AppData\Local\Programs\Python\Python314\Scripts\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return "ffmpeg"

    def run_ffprobe(self, file_path: str) -> Dict[str, Any]:
        """Runs ffprobe securely with argument list and extracts full JSON metadata."""
        ffprobe_bin = self._find_ffprobe_cmd()
        cmd = [
            ffprobe_bin,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            "-show_chapters",
            file_path
        ]
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=settings.FFMPEG_TIMEOUT_SECONDS,
                check=False
            )
            if res.returncode != 0:
                print(f"[MetadataService] ffprobe non-zero return: {res.stderr}")
                return {}
            return json.loads(res.stdout or "{}")
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=504, detail="FFprobe inspection timed out.")
        except Exception as e:
            print(f"[MetadataService] Error running ffprobe: {e}")
            return {}

    def extract_summary(self, raw: Dict[str, Any], filename: str, file_path: str) -> Dict[str, Any]:
        """Parses raw FFprobe JSON into structured fields."""
        format_info = raw.get("format", {})
        streams = raw.get("streams", [])
        chapters = raw.get("chapters", [])

        # Find video & audio streams
        video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

        width = video_stream.get("width") if video_stream else None
        height = video_stream.get("height") if video_stream else None
        dimensions = f"{width}x{height}" if width and height else None

        format_tags = format_info.get("tags", {})
        stream_tags = {}
        for s in streams:
            idx = s.get("index", 0)
            if "tags" in s and s["tags"]:
                stream_tags[f"stream_{idx}"] = s["tags"]

        creation_time = (
            format_tags.get("creation_time") or
            format_tags.get("date") or
            (video_stream.get("tags", {}).get("creation_time") if video_stream else None)
        )
        encoder = (
            format_tags.get("encoder") or
            format_tags.get("major_brand") or
            (video_stream.get("tags", {}).get("handler_name") if video_stream else None)
        )
        location = (
            format_tags.get("location") or
            format_tags.get("location-eng") or
            format_tags.get("com.apple.quicktime.location.ISO6709")
        )

        try:
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else int(format_info.get("size", 0))
        except Exception:
            file_size = int(format_info.get("size", 0) or 0)

        duration = None
        try:
            if "duration" in format_info:
                duration = round(float(format_info["duration"]), 2)
            elif video_stream and "duration" in video_stream:
                duration = round(float(video_stream["duration"]), 2)
        except Exception:
            pass

        return {
            "filename": filename,
            "file_size_bytes": file_size,
            "container_format": format_info.get("format_long_name") or format_info.get("format_name") or "Unknown",
            "duration_seconds": duration,
            "dimensions": dimensions,
            "width": width,
            "height": height,
            "video_codec": video_stream.get("codec_name") if video_stream else None,
            "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
            "creation_time": creation_time,
            "encoder": encoder,
            "location": location,
            "container_tags": format_tags,
            "stream_tags": stream_tags,
            "chapters_count": len(chapters),
            "raw_metadata": raw
        }

    async def save_uploaded_temp(self, file: UploadFile) -> Tuple[str, str]:
        """Safely saves uploaded video to a unique temporary file."""
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        temp_id = uuid.uuid4().hex
        ext = os.path.splitext(file.filename or "")[1].lower()
        if not ext or ext not in [".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"]:
            ext = ".mp4"
        temp_filename = f"upload_{temp_id}{ext}"
        temp_path = os.path.join(self.temp_dir, temp_filename)

        total_bytes = 0
        await file.seek(0)
        with open(temp_path, "wb") as f:
            while True:
                chunk = await file.read(64 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds permitted size of {settings.MAX_UPLOAD_SIZE_MB} MB."
                    )
                f.write(chunk)

        return temp_path, file.filename or "video.mp4"

    async def inspect(self, file: UploadFile, db: Optional[Session] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Saves temporary file, runs FFprobe, extracts metadata and cleans up temp upload."""
        temp_path, original_filename = await self.save_uploaded_temp(file)
        try:
            raw = self.run_ffprobe(temp_path)
            if not raw or not raw.get("format"):
                raise HTTPException(status_code=400, detail="Invalid video file or metadata unreadable by FFprobe.")
            summary = self.extract_summary(raw, original_filename, temp_path)

            if db:
                log = SecurityLog(
                    user_id=user_id,
                    event_type="metadata_inspected",
                    details={"filename": original_filename, "container": summary["container_format"]}
                )
                db.add(log)
                db.commit()

            return summary
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def inspect_file_path(self, file_path: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """Inspects video metadata directly from a local filepath on disk."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        raw = self.run_ffprobe(file_path)
        if not raw or not raw.get("format"):
            raise HTTPException(status_code=400, detail="Invalid video file or metadata unreadable by FFprobe.")
        return self.extract_summary(raw, filename or os.path.basename(file_path), file_path)

    def sanitize_file_path(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        original_filename: str = "video.mp4"
    ) -> Dict[str, Any]:
        """
        Core sanitization pipeline:
        1. Inspects original metadata via FFprobe
        2. Applies FFmpeg metadata stripping (-map_metadata -1 -map_chapters -1 -fflags +bitexact)
        3. Falls back to compatible re-encoding only if stream copying fails
        4. Verifies output validity and stream integrity
        5. Performs before-and-after metadata comparison
        6. Computes SHA-256 hash of the exact output file
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input video file not found: {input_path}")

        ffmpeg_bin = self._find_ffmpeg_cmd()
        ext = os.path.splitext(input_path)[1].lower() or ".mp4"

        if not output_path:
            job_id = uuid.uuid4().hex
            sanitized_filename = f"sanitized_{job_id[:8]}{ext}"
            output_path = os.path.join(self.sanitized_dir, sanitized_filename)
        else:
            sanitized_filename = os.path.basename(output_path)
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # 1. Inspect original with FFprobe
        orig_raw = self.run_ffprobe(input_path)
        if not orig_raw or not orig_raw.get("format"):
            raise HTTPException(status_code=400, detail="Unable to inspect original video metadata with FFprobe.")
        orig_summary = self.extract_summary(orig_raw, original_filename, input_path)

        # 2. Run FFmpeg sanitization
        # -map 0 ensures all streams (video, audio) are mapped
        # -map_metadata -1 removes container metadata
        # -map_chapters -1 removes chapters
        # -fflags +bitexact -flags:v +bitexact -flags:a +bitexact prevents writing encoder timestamp/tags
        cmd_copy = [
            ffmpeg_bin, "-y",
            "-i", os.path.abspath(input_path),
            "-map", "0",
            "-map_metadata", "-1",
            "-map_chapters", "-1",
            "-fflags", "+bitexact",
            "-flags:v", "+bitexact",
            "-flags:a", "+bitexact",
            "-c", "copy",
            os.path.abspath(output_path)
        ]

        res = subprocess.run(
            cmd_copy,
            capture_output=True,
            text=True,
            timeout=settings.FFMPEG_TIMEOUT_SECONDS,
            check=False
        )

        needs_reencode = False
        if res.returncode != 0 or not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            needs_reencode = True
        else:
            test_probe = self.run_ffprobe(output_path)
            if not test_probe or not test_probe.get("format"):
                needs_reencode = True

        if needs_reencode:
            print(f"[MetadataService] Stream copy failed or unreadable, re-encoding for compatibility: {res.stderr}")
            cmd_fallback = [
                ffmpeg_bin, "-y",
                "-i", os.path.abspath(input_path),
                "-map_metadata", "-1",
                "-map_chapters", "-1",
                "-fflags", "+bitexact",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "18",
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                os.path.abspath(output_path)
            ]
            res_fallback = subprocess.run(
                cmd_fallback,
                capture_output=True,
                text=True,
                timeout=settings.FFMPEG_TIMEOUT_SECONDS,
                check=False
            )
            if res_fallback.returncode != 0 or not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"FFmpeg sanitization failed: {res_fallback.stderr[:300] if res_fallback.stderr else 'Unknown error'}"
                )

        # 3. Output verification using FFprobe
        sanitized_raw = self.run_ffprobe(output_path)
        if not sanitized_raw or not sanitized_raw.get("format"):
            raise HTTPException(status_code=500, detail="Sanitized output verification failed: Output unreadable by FFprobe.")

        sanitized_summary = self.extract_summary(sanitized_raw, sanitized_filename, output_path)

        # Verify stream fidelity
        orig_has_video = any(s.get("codec_type") == "video" for s in orig_raw.get("streams", []))
        orig_has_audio = any(s.get("codec_type") == "audio" for s in orig_raw.get("streams", []))
        san_has_video = any(s.get("codec_type") == "video" for s in sanitized_raw.get("streams", []))
        san_has_audio = any(s.get("codec_type") == "audio" for s in sanitized_raw.get("streams", []))

        if orig_has_video and not san_has_video:
            raise HTTPException(status_code=500, detail="Sanitization verification failed: Video stream was dropped.")
        if orig_has_audio and not san_has_audio:
            raise HTTPException(status_code=500, detail="Sanitization verification failed: Audio stream was dropped.")

        # 4. Generate before-and-after comparison
        removed_fields = []
        retained_fields = []
        unverified_fields = []
        comparison_details = []

        # Check creation_time
        if orig_summary.get("creation_time"):
            if not sanitized_summary.get("creation_time"):
                removed_fields.append("Creation Timestamp (creation_time)")
                comparison_details.append({
                    "field": "Creation Timestamp",
                    "original": str(orig_summary.get("creation_time")),
                    "sanitized": "Removed",
                    "status": "Removed"
                })
            else:
                comparison_details.append({
                    "field": "Creation Timestamp",
                    "original": str(orig_summary.get("creation_time")),
                    "sanitized": str(sanitized_summary.get("creation_time")),
                    "status": "Retained"
                })

        # Check encoder / software
        if orig_summary.get("encoder"):
            if not sanitized_summary.get("encoder") or sanitized_summary.get("encoder") != orig_summary.get("encoder"):
                removed_fields.append("Encoder / Software Identifying Tag")
                comparison_details.append({
                    "field": "Encoder / Software Tag",
                    "original": str(orig_summary.get("encoder")),
                    "sanitized": str(sanitized_summary.get("encoder")) if sanitized_summary.get("encoder") else "Removed",
                    "status": "Sanitized"
                })
            else:
                comparison_details.append({
                    "field": "Encoder / Software Tag",
                    "original": str(orig_summary.get("encoder")),
                    "sanitized": str(sanitized_summary.get("encoder")),
                    "status": "Retained"
                })

        # Check location
        if orig_summary.get("location"):
            if not sanitized_summary.get("location"):
                removed_fields.append("GPS / Geolocation Metadata")
                comparison_details.append({
                    "field": "Geolocation",
                    "original": str(orig_summary.get("location")),
                    "sanitized": "Removed",
                    "status": "Removed"
                })
            else:
                comparison_details.append({
                    "field": "Geolocation",
                    "original": str(orig_summary.get("location")),
                    "sanitized": str(sanitized_summary.get("location")),
                    "status": "Retained"
                })

        # Check container tags
        orig_tags = orig_summary.get("container_tags", {})
        san_tags = sanitized_summary.get("container_tags", {})
        for k, v in orig_tags.items():
            if k not in ["major_brand", "minor_version", "compatible_brands"]:
                if k not in san_tags:
                    removed_fields.append(f"Tag: {k}")
                    comparison_details.append({
                        "field": f"Container Tag ({k})",
                        "original": str(v),
                        "sanitized": "Removed",
                        "status": "Removed"
                    })
                else:
                    comparison_details.append({
                        "field": f"Container Tag ({k})",
                        "original": str(v),
                        "sanitized": str(san_tags[k]),
                        "status": "Retained"
                    })

        # Check chapters
        if orig_summary.get("chapters_count", 0) > 0:
            if sanitized_summary.get("chapters_count", 0) == 0:
                removed_fields.append(f"Chapters ({orig_summary.get('chapters_count')} chapters)")
                comparison_details.append({
                    "field": "Chapters",
                    "original": f"{orig_summary.get('chapters_count')} chapters",
                    "sanitized": "0 chapters",
                    "status": "Removed"
                })

        # Audio/Video Streams Retained
        retained_fields.append(f"Video Stream ({sanitized_summary.get('video_codec', 'video')} {sanitized_summary.get('dimensions', '')})")
        if sanitized_summary.get("audio_codec"):
            retained_fields.append(f"Audio Stream ({sanitized_summary.get('audio_codec')})")

        # 5. Calculate SHA-256 hash of the exact final output file
        from app.services.integrity_service import integrity_service
        hash_info = integrity_service.calculate_filepath_hash(output_path, filename=sanitized_filename)
        sha256_hash = hash_info["sha256_hash"]

        # Truthful status determination
        has_removable_orig = bool(
            orig_summary.get("creation_time") or
            orig_summary.get("location") or
            orig_summary.get("chapters_count", 0) > 0 or
            any(k not in ["major_brand", "minor_version", "compatible_brands"] for k in orig_tags.keys())
        )

        if not has_removable_orig and len(removed_fields) == 0:
            verification_status = "clean_original"
            status_text = "Video ready. No removable metadata was detected in the original file."
            summary_text = (
                f"Video output verified ({sanitized_summary.get('dimensions', '')}). "
                f"No removable metadata was detected in the source video."
            )
        elif any(d["status"] == "Retained" for d in comparison_details):
            verification_status = "partial"
            status_text = "Video ready. Some supported metadata was removed, but certain metadata fields remain."
            summary_text = (
                f"Removed {len(removed_fields)} identifying metadata fields while preserving full "
                f"{sanitized_summary.get('dimensions', '')} video and audio stream fidelity."
            )
        else:
            verification_status = "verified"
            status_text = "Video ready. Supported metadata sanitization was completed and the output was verified."
            summary_text = (
                f"Successfully sanitized video container. Removed {len(removed_fields)} identifying tags/fields while "
                f"preserving full {sanitized_summary.get('dimensions', '')} video and audio playback stream fidelity."
            )

        return {
            "sanitized_path": output_path,
            "sanitized_filename": sanitized_filename,
            "sha256_hash": sha256_hash,
            "file_size_bytes": hash_info["bytes_processed"],
            "verification_status": verification_status,
            "status_text": status_text,
            "original": orig_summary,
            "sanitized": sanitized_summary,
            "comparison": {
                "removed_fields": removed_fields,
                "retained_fields": retained_fields,
                "unverified_fields": unverified_fields,
                "details": comparison_details
            },
            "summary": summary_text
        }

    async def sanitize(
        self,
        file: UploadFile,
        db: Session,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Inspects original metadata, runs FFmpeg with -map_metadata -1 to strip metadata,
        inspects sanitized output, generates before-and-after comparison, calculates SHA-256,
        and saves job for download.
        """
        temp_path, original_filename = await self.save_uploaded_temp(file)
        job_id = uuid.uuid4().hex
        ext = os.path.splitext(original_filename)[1].lower() or ".mp4"
        sanitized_filename = f"sanitized_{job_id[:8]}{ext}"
        sanitized_path = os.path.join(self.sanitized_dir, sanitized_filename)

        try:
            result = self.sanitize_file_path(
                input_path=temp_path,
                output_path=sanitized_path,
                original_filename=original_filename
            )

            # 5. Save job to database
            now = utc_now()
            expires_at = now + timedelta(hours=settings.METADATA_RETENTION_HOURS)
            metadata_job = MetadataJob(
                job_id=job_id,
                user_id=user_id,
                original_filename=original_filename,
                sanitized_filename=sanitized_filename,
                sanitized_path=sanitized_path,
                original_metadata=result["original"],
                sanitized_metadata=result["sanitized"],
                comparison=result["comparison"],
                created_at=now,
                expires_at=expires_at
            )
            db.add(metadata_job)

            # Security log
            log = SecurityLog(
                user_id=user_id,
                event_type="metadata_sanitized",
                details={
                    "job_id": job_id,
                    "filename": original_filename,
                    "removed_count": len(result["comparison"]["removed_fields"]),
                    "sha256": result["sha256_hash"]
                }
            )
            db.add(log)
            db.commit()

            return {
                "job_id": job_id,
                "original_filename": original_filename,
                "sanitized_filename": sanitized_filename,
                "sha256_hash": result["sha256_hash"],
                "status": result["status_text"],
                "download_url": f"/api/security/metadata/download/{job_id}",
                "original": result["original"],
                "sanitized": result["sanitized"],
                "comparison": result["comparison"],
                "summary": result["summary"]
            }
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def get_download_file(self, db: Session, job_id: str, user_id: Optional[int] = None) -> FileResponse:
        """Validates job ID and user authorization and returns sanitized video file."""
        job = db.query(MetadataJob).filter(MetadataJob.job_id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Sanitization job not found or expired.")

        # User authorization check
        if job.user_id is not None and user_id is not None and job.user_id != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized access to this sanitized file.")

        if not os.path.exists(job.sanitized_path):
            raise HTTPException(status_code=404, detail="Sanitized video file is no longer available.")

        return FileResponse(
            path=job.sanitized_path,
            filename=job.sanitized_filename,
            media_type="video/mp4"
        )

metadata_service = MetadataService()
