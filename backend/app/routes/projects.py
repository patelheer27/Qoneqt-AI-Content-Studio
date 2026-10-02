import json
import logging
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.config import settings
from app.database.session import get_db
from app.models.project import Project
from app.models.scene import Scene
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectStatusResponse,
    SceneResponse,
    PublishResponse
)
from app.services.pipeline_service import PipelineService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])

def serialize_project(project: Project, request: Optional[Request] = None) -> ProjectResponse:
    hashtags_list = []
    if project.hashtags:
        try:
            hashtags_list = json.loads(project.hashtags)
        except Exception:
            hashtags_list = [h.strip() for h in project.hashtags.split() if h.strip()]

    video_url = None
    if project.video_path and Path(project.video_path).exists():
        video_url = f"/api/projects/{project.id}/video"

    return ProjectResponse(
        id=project.id,
        topic=project.topic,
        platform=project.platform or "Qoneqt Global Feed",
        duration=project.duration or 30,
        tone=project.tone or "Educational",
        title=project.title,
        hook=project.hook,
        summary=project.summary,
        script=project.script,
        caption=project.caption,
        hashtags=hashtags_list,
        status=project.status,
        stage=project.stage,
        progress=project.progress,
        error_message=project.error_message,
        video_path=project.video_path,
        video_url=video_url,
        created_at=project.created_at,
        updated_at=project.updated_at,
        scenes=[SceneResponse.model_validate(sc) for sc in project.scenes]
    )

@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    """Creates a new project record and prepares it for pipeline processing"""
    project = Project(
        topic=payload.topic.strip(),
        platform=payload.platform or "Qoneqt Global Feed",
        duration=payload.duration or 30,
        tone=payload.tone or "Educational",
        status="created",
        stage="initialized",
        progress=0
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return serialize_project(project)

@router.post("/{project_id}/generate", response_model=ProjectStatusResponse)
async def generate_project(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Triggers the asynchronous AI video generation pipeline"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.status = "processing"
    project.stage = "analyzing_topic"
    project.progress = 5
    project.error_message = None
    db.commit()

    # Launch background task
    background_tasks.add_task(PipelineService.run_pipeline, project.id)

    return ProjectStatusResponse(
        project_id=project.id,
        status=project.status,
        stage=project.stage,
        progress=project.progress
    )

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    """Retrieves full project details including all scene components"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return serialize_project(project)

@router.get("/{project_id}/status", response_model=ProjectStatusResponse)
def get_project_status(project_id: str, db: Session = Depends(get_db)):
    """Returns the current pipeline status and completion percentage"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    video_url = f"/api/projects/{project.id}/video" if project.video_path and Path(project.video_path).exists() else None

    return ProjectStatusResponse(
        project_id=project.id,
        status=project.status,
        stage=project.stage,
        progress=project.progress,
        error_message=project.error_message,
        video_url=video_url
    )

@router.get("/{project_id}/video")
def get_project_video(project_id: str, db: Session = Depends(get_db)):
    """Streams the rendered MP4 video file directly to the client video player"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or not project.video_path:
        raise HTTPException(status_code=404, detail="Video not found for this project")

    file_path = Path(project.video_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file does not exist on disk")

    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
        filename=f"qoneqt_{project.id[:8]}.mp4"
    )

@router.get("", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    """Lists all previously created projects, newest first"""
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return [serialize_project(p) for p in projects]

@router.post("/{project_id}/publish", response_model=PublishResponse)
def publish_project(project_id: str, db: Session = Depends(get_db)):
    """Simulates publishing the finished video to Qoneqt Global Feed"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.video_path or not Path(project.video_path).exists():
        raise HTTPException(status_code=400, detail="Cannot publish: Video has not been rendered yet")

    project.status = "published"
    project.updated_at = datetime.now(timezone.utc)
    db.commit()

    return PublishResponse(
        project_id=project.id,
        title=project.title or project.topic,
        status="published",
        platform=project.platform or "Qoneqt Global Feed",
        published_at=datetime.now(timezone.utc),
        video_url=f"/api/projects/{project.id}/video",
        message=f"Successfully published to {project.platform or 'Qoneqt Global Feed'}!"
    )
