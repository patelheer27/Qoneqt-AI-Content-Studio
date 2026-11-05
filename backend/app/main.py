from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.database import engine, Base
from app.models.project import Project
from app.models.image_to_video import ImageToVideoProject
from app.models.user import User, OTPRecord, SessionRecord, RecoveryCode
from app.models.security import MetadataJob, SecurityLog, MalwareScanRecord
from app.routes import projects, auth, security, image_to_video

# Create database tables
Base.metadata.create_all(bind=engine)

# Auto-migration for sqlite to ensure new columns exist in existing tables
from sqlalchemy import text
with engine.connect() as conn:
    for col_def in [
        ("social_post", "JSON"),
        ("raw_output_path", "VARCHAR"),
        ("metadata_policy", "VARCHAR DEFAULT 'sanitized'"),
        ("sanitize_metadata", "BOOLEAN DEFAULT 1"),
        ("metadata_info", "JSON")
    ]:
        try:
            conn.execute(text(f"ALTER TABLE projects ADD COLUMN {col_def[0]} {col_def[1]}"))
            conn.commit()
        except Exception:
            pass

    # MFA columns on users table
    for col_def in [
        ("totp_secret_enc", "VARCHAR(512)"),
        ("mfa_enabled", "BOOLEAN DEFAULT 0"),
        ("last_totp_step", "INTEGER"),
        ("failed_attempts", "INTEGER DEFAULT 0"),
        ("locked_until", "DATETIME")
    ]:
        try:
            conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_def[0]} {col_def[1]}"))
            conn.commit()
        except Exception:
            pass

app = FastAPI(title="Qoneqt AI Content Studio API", version="2.0.0")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure storage directories exist
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
storage_dir = os.path.join(BASE_DIR, "storage")
quarantine_dir = os.path.join(BASE_DIR, "quarantine")
os.makedirs(os.path.join(storage_dir, "renders"), exist_ok=True)
os.makedirs(os.path.join(storage_dir, "renders", "sanitized"), exist_ok=True)
os.makedirs(os.path.join(storage_dir, "assets"), exist_ok=True)
os.makedirs(os.path.join(storage_dir, "assets", "uploads"), exist_ok=True)
os.makedirs(os.path.join(storage_dir, "assets", "audio"), exist_ok=True)
os.makedirs(os.path.join(storage_dir, "assets", "music"), exist_ok=True)
os.makedirs(os.path.join(storage_dir, "temp"), exist_ok=True)
os.makedirs(quarantine_dir, exist_ok=True)

# Mount static files to serve the generated videos and assets (quarantine is NOT mounted)
app.mount("/storage", StaticFiles(directory=storage_dir), name="storage")

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(security.router, prefix="/api/security", tags=["security"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(image_to_video.router, prefix="/api/image-to-video", tags=["image-to-video"])

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "Qoneqt AI Content Studio API"}

