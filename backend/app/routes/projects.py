import os
import re
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse, StrategySchema, MetadataPolicyRequest, RenderVideoRequest
from app.services.llm_service import llm_service
from app.services.metadata_service import metadata_service
from app.services.integrity_service import integrity_service

router = APIRouter()

def apply_project_metadata_policy(project: Project, sanitize: bool, db: Session) -> Project:
    """
    Applies metadata policy (sanitization or preservation) to a project's rendered video.
    Locates the source video, runs FFmpeg sanitization or FFprobe inspection,
    verifies streams and output fidelity, calculates exact SHA-256, and prepares download path.
    """
    source_video = project.raw_output_path or project.output_path
    project.sanitize_metadata = sanitize

    if not source_video:
        project.metadata_policy = "sanitized" if sanitize else "preserved"
        return project

    file_path = source_video
    if not os.path.isabs(file_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if not os.path.exists(file_path):
            alt_path = os.path.join(base_dir, file_path)
            if os.path.exists(alt_path):
                file_path = alt_path

    if not os.path.exists(file_path):
        return project

    if not project.raw_output_path:
        project.raw_output_path = file_path

    if sanitize:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sanitized_dir = os.path.join(base_dir, "storage", "renders", "sanitized")
        os.makedirs(sanitized_dir, exist_ok=True)
        sanitized_filename = f"sanitized_proj_{project.id}_{uuid.uuid4().hex[:8]}.mp4"
        sanitized_path = os.path.join(sanitized_dir, sanitized_filename)

        san_res = metadata_service.sanitize_file_path(
            input_path=file_path,
            output_path=sanitized_path,
            original_filename=f"{project.topic or 'video'}.mp4"
        )

        project.output_path = sanitized_path
        project.metadata_policy = "sanitized"
        project.metadata_info = {
            "policy": "sanitized",
            "policy_label": "Sanitization enabled",
            "status": san_res["verification_status"],
            "status_label": "Verified",
            "output_label": "Sanitized video ready",
            "sha256": san_res["sha256_hash"],
            "file_size_bytes": san_res["file_size_bytes"],
            "comparison": san_res["comparison"],
            "original_metadata": san_res["original"],
            "sanitized_metadata": san_res["sanitized"],
            "summary": san_res["summary"],
            "status_text": san_res["status_text"]
        }
    else:
        raw_file = project.raw_output_path or file_path
        project.output_path = raw_file
        project.metadata_policy = "preserved"

        orig_info = metadata_service.inspect_file_path(raw_file, filename=os.path.basename(raw_file))
        hash_info = integrity_service.calculate_filepath_hash(raw_file)
        project.metadata_info = {
            "policy": "preserved",
            "policy_label": "Original metadata preserved",
            "status": "video_ready",
            "status_label": "Video ready",
            "output_label": "Original-metadata video ready",
            "sha256": hash_info["sha256_hash"],
            "file_size_bytes": hash_info["bytes_processed"],
            "original_metadata": orig_info,
            "summary": "Metadata sanitization was disabled for this export. Original metadata was preserved where possible through the export pipeline.",
            "status_text": "Video ready. Metadata sanitization was disabled for this export. Metadata may remain."
        }

    return project

@router.post("/", response_model=ProjectResponse)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    data = project.dict()
    # Default to 16:9 for YouTube horizontal videos
    if data.get("platform") == "YouTube" and (not data.get("aspect_ratio") or data.get("aspect_ratio") == "9:16"):
        data["aspect_ratio"] = "16:9"
    db_project = Project(**data)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/", response_model=list[ProjectResponse])
def get_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.created_at.desc()).all()

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # If video is already completed but social post hasn't been generated yet, auto-generate it
    if project.status == "Completed" and not project.social_post:
        try:
            hook = ""
            if project.script and isinstance(project.script, dict):
                hook = project.script.get("hook", "")
            if not hook and project.strategy and isinstance(project.strategy, dict):
                hook = project.strategy.get("hook", "")

            social_post = llm_service.generate_social_post(
                topic=project.topic,
                title=project.title or (project.strategy.get("title") if project.strategy else project.topic),
                hook=hook,
                platform=project.platform or "YouTube Shorts",
                audience=project.audience or "General Audience",
                goal=project.goal or "Educate",
                tone=project.tone or "Educational",
                language=project.language or "English"
            )
            project.social_post = social_post
            db.commit()
            db.refresh(project)
        except Exception as e:
            print(f"[get_project] Could not auto-generate social post: {e}")

    # Auto-populate metadata_info for completed projects if missing
    if project.status == "Completed" and project.output_path and not project.metadata_info:
        try:
            apply_project_metadata_policy(project, project.sanitize_metadata is not False, db)
            db.commit()
            db.refresh(project)
        except Exception as me:
            print(f"[get_project] Could not populate metadata info: {me}")

    return project

@router.post("/{project_id}/director")
def generate_director_strategy(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Generate both strategy and initial script together in ONE unified AI call
    res = llm_service.generate_strategy_and_script(
        topic=project.topic,
        audience=project.audience or "General Audience",
        platform=project.platform or "YouTube Shorts",
        duration=project.duration or 60,
        goal=project.goal or "Educate",
        tone=project.tone or "Educational",
        language=project.language or "English"
    )
    
    strategy = res.get("strategy", {})
    script = res.get("script", {})
    
    project.strategy = strategy
    if script and script.get("scenes"):
        project.script = script
        project.scenes = script.get("scenes", [])
        project.status = "Ready"
    else:
        project.status = "Planning"

    if strategy and strategy.get("title"):
        project.title = strategy["title"]
    db.commit()
    db.refresh(project)
    
    return project

@router.put("/{project_id}/strategy", response_model=ProjectResponse)
def update_strategy(project_id: int, strategy: dict, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.strategy = strategy
    if strategy and strategy.get("title"):
        project.title = strategy["title"]
    db.commit()
    db.refresh(project)
    return project

@router.put("/{project_id}/language", response_model=ProjectResponse)
def update_language(project_id: int, payload: dict, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    new_lang = payload.get("language")
    if new_lang:
        project.language = new_lang
        if payload.get("regenerate_strategy", False):
            strategy = llm_service.generate_strategy(
                topic=project.topic,
                audience=project.audience or "General Audience",
                platform=project.platform or "YouTube Shorts",
                duration=project.duration or 60,
                goal=project.goal or "Educate",
                tone=project.tone or "Educational",
                language=project.language
            )
            project.strategy = strategy
            if strategy and strategy.get("title"):
                project.title = strategy["title"]
        db.commit()
        db.refresh(project)
    return project

@router.post("/{project_id}/generate-script")
def generate_script(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.strategy:
        # If strategy hasn't been generated yet, generate strategy and script together
        res = llm_service.generate_strategy_and_script(
            topic=project.topic,
            audience=project.audience or "General Audience",
            platform=project.platform or "YouTube Shorts",
            duration=project.duration or 60,
            goal=project.goal or "Educate",
            tone=project.tone or "Educational",
            language=project.language or "English"
        )
        project.strategy = res.get("strategy", {})
        script_data = res.get("script", {})
        if project.strategy and project.strategy.get("title"):
            project.title = project.strategy["title"]
    else:
        script_data = llm_service.generate_script(
            topic=project.topic,
            strategy=project.strategy,
            audience=project.audience or "General Audience",
            goal=project.goal or "Educate",
            tone=project.tone or "Educational",
            platform=project.platform or "YouTube Shorts",
            language=project.language or "English",
            force_regenerate=True
        )
    
    project.script = script_data
    project.scenes = script_data.get("scenes", [])
    if script_data.get("title") and (not project.title or project.title == "Untitled Project"):
        project.title = script_data["title"]
    project.status = "Ready"

    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(project, "script")
    flag_modified(project, "scenes")
    db.commit()
    db.refresh(project)
    
    return project

@router.put("/{project_id}/script", response_model=ProjectResponse)
def update_script(project_id: int, script: dict, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.script = script
    project.scenes = script.get("scenes", [])
    db.commit()
    db.refresh(project)
    return project

from app.services.image_service import image_service
from app.services.tts_service import tts_service
from app.services.video_service import video_service
import asyncio

@router.post("/{project_id}/render")
def render_video(
    project_id: int, 
    payload: Optional[RenderVideoRequest] = None, 
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.scenes:
        raise HTTPException(status_code=400, detail="No scenes found in the script")
    
    project.status = "Rendering"
    db.commit()
    
    # In a real app this would be a background task (e.g. Celery).
    # For now, we do it synchronously to keep it simple.
    try:
        scene_video_paths = []
        target_aspect = project.aspect_ratio or ("16:9" if project.platform == "YouTube" else "9:16")
        if project.platform == "YouTube" and target_aspect == "9:16":
            target_aspect = "16:9"
            project.aspect_ratio = "16:9"
            db.commit()
        for idx, scene in enumerate(project.scenes, 1):
            narration_text = (scene.get("narration") or "").strip()
            # Title for top badge: prioritize on_screen_text, or project title
            title_text = (scene.get("on_screen_text") or "").strip()
            if not title_text:
                title_text = project.title if idx == 1 else f"Scene {idx}"

            # 1. Generate Voiceover Audio FIRST
            voice_style = (project.strategy.get("voice_style", "Default") if project.strategy else "Default")
            audio_path = tts_service.generate_voiceover(
                text=narration_text or "Welcome to this scene.",
                voice_style=voice_style,
                language=project.language or "English"
            )

            # 2. Get exact duration of the generated speech audio
            # Concise 0.35s breathing buffer so cuts are snappy with no awkward dead silence
            audio_dur = video_service.get_audio_duration(audio_path)
            if audio_dur > 0:
                exact_duration = round(audio_dur + 0.35, 2)
            else:
                exact_duration = max(float(scene.get("duration") or 4.0), 2.5)
            scene["duration"] = exact_duration

            # 3. Generate Visual with Top Title and Lower-Third Speech Caption
            img_path = image_service.generate_scene_visual(
                description=scene.get("visual_description", "") or narration_text or project.topic,
                title=title_text,
                caption=narration_text,
                aspect_ratio=target_aspect,
                scene_index=idx,
                topic=project.topic
            )

            # 4. Render Scene Video
            scene_video_path = video_service.render_scene(
                media_path=img_path,
                audio_path=audio_path,
                duration=exact_duration,
                aspect_ratio=target_aspect
            )
            scene_video_paths.append(scene_video_path)

        # Update scene durations in database with explicit SQLAlchemy change tracking
        from sqlalchemy.orm.attributes import flag_modified
        project.scenes = [dict(s) for s in project.scenes]
        flag_modified(project, "scenes")
        db.commit()
            
        # 4. Concatenate
        final_video = video_service.concatenate_scenes(scene_video_paths)
        project.raw_output_path = final_video
        project.output_path = final_video
        project.status = "Completed"

        # Apply metadata policy (default: True / enabled)
        should_sanitize = True
        if payload and payload.sanitize_metadata is not None:
            should_sanitize = payload.sanitize_metadata
        elif project.sanitize_metadata is not None:
            should_sanitize = project.sanitize_metadata

        apply_project_metadata_policy(project, should_sanitize, db)

        # Generate caption and hashtags based on video topic so they are ready for download & posting
        try:
            hook = ""
            if project.script and isinstance(project.script, dict):
                hook = project.script.get("hook", "")
            if not hook and project.strategy and isinstance(project.strategy, dict):
                hook = project.strategy.get("hook", "")

            project.social_post = llm_service.generate_social_post(
                topic=project.topic,
                title=project.title or (project.strategy.get("title") if project.strategy else project.topic),
                hook=hook,
                platform=project.platform or "YouTube Shorts",
                audience=project.audience or "General Audience",
                goal=project.goal or "Educate",
                tone=project.tone or "Educational",
                language=project.language or "English"
            )
        except Exception as se:
            print(f"[Render] Warning generating social post: {se}")

        db.commit()
        db.refresh(project)
        return {
            "status": "success", 
            "output_path": project.output_path, 
            "social_post": project.social_post,
            "metadata_policy": project.metadata_policy,
            "metadata_info": project.metadata_info
        }
        
    except Exception as e:
        print(f"Rendering failed: {e}")
        project.status = "Failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Rendering failed: {str(e)}")


@router.post("/{project_id}/metadata-policy", response_model=ProjectResponse)
def update_project_metadata_policy(
    project_id: int,
    payload: MetadataPolicyRequest,
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    updated = apply_project_metadata_policy(project, payload.sanitize_metadata, db)
    db.commit()
    db.refresh(updated)
    return updated


@router.get("/{project_id}/checksum")
def download_project_checksum(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.output_path:
        raise HTTPException(status_code=404, detail="Video file not found or not rendered yet")

    file_path = project.output_path
    if not os.path.isabs(file_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        alt_path = os.path.join(base_dir, file_path)
        if os.path.exists(alt_path):
            file_path = alt_path

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    hash_info = integrity_service.calculate_filepath_hash(file_path)
    sha256 = hash_info["sha256_hash"]

    raw_name = project.topic or (project.strategy.get("title") if project.strategy else None) or "video"
    safe_name = re.sub(r'[^\w\- ]+', '', raw_name, flags=re.UNICODE).strip().replace(' ', '_')
    filename = f"{safe_name or 'video'}.mp4"

    content = f"{sha256}  {filename}\n"
    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{safe_name or "video"}.sha256"'}
    )


@router.post("/{project_id}/generate-social-post", response_model=ProjectResponse)
def generate_project_social_post(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    hook = ""
    if project.script and isinstance(project.script, dict):
        hook = project.script.get("hook", "")
    if not hook and project.strategy and isinstance(project.strategy, dict):
        hook = project.strategy.get("hook", "")

    social_post = llm_service.generate_social_post(
        topic=project.topic,
        title=project.title or (project.strategy.get("title") if project.strategy else project.topic),
        hook=hook,
        platform=project.platform or "YouTube Shorts",
        audience=project.audience or "General Audience",
        goal=project.goal or "Educate",
        tone=project.tone or "Educational",
        language=project.language or "English"
    )
    project.social_post = social_post
    db.commit()
    db.refresh(project)
    return project


@router.put("/{project_id}/social-post", response_model=ProjectResponse)
def update_project_social_post(project_id: int, social_post: dict, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.social_post = social_post
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}/download")
def download_video(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.output_path:
        raise HTTPException(status_code=404, detail="Video file not found or not rendered yet")
    
    file_path = project.output_path
    if not os.path.isabs(file_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        alt_path = os.path.join(base_dir, file_path)
        if os.path.exists(alt_path):
            file_path = alt_path
        else:
            raise HTTPException(status_code=404, detail="Video file not found or not rendered yet")
    elif not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video file not found or not rendered yet")
    
    # Create clean safe filename from topic or title
    raw_name = project.topic or (project.strategy.get("title") if project.strategy else None) or "video"
    safe_name = re.sub(r'[^\w\- ]+', '', raw_name, flags=re.UNICODE).strip().replace(' ', '_')
    filename = f"{safe_name or 'video'}.mp4"
    
    return FileResponse(
        path=os.path.abspath(file_path),
        media_type="video/mp4",
        filename=filename
    )
