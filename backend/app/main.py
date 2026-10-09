from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.database import engine, Base
from app.routes import projects

# Create database tables
Base.metadata.create_all(bind=engine)

# Auto-migration for sqlite to ensure new columns exist in existing tables
from sqlalchemy import text
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE projects ADD COLUMN social_post JSON"))
        conn.commit()
    except Exception:
        pass

app = FastAPI(title="AI Video Studio API", version="1.0.0")

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
os.makedirs(os.path.join(storage_dir, "renders"), exist_ok=True)
os.makedirs(os.path.join(storage_dir, "assets"), exist_ok=True)

# Mount static files to serve the generated videos and assets
app.mount("/storage", StaticFiles(directory=storage_dir), name="storage")

app.include_router(projects.router, prefix="/api/projects", tags=["projects"])

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}
