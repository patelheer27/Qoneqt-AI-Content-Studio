import os
import re
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse, StrategySchema
from app.services.llm_service import llm_service

router = APIRouter()

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

    return project

@router.post("/{project_id}/director")
def generate_director_strategy(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    strategy = llm_service.generate_strategy(
        topic=project.topic,
        audience=project.audience or "General Audience",
        platform=project.platform or "YouTube Shorts",
        duration=project.duration or 60,
        goal=project.goal or "Educate",
        tone=project.tone or "Educational",
        language=project.language or "English"
    )
    
    project.strategy = strategy
    if strategy and strategy.get("title"):
        project.title = strategy["title"]
    project.status = "Planning"
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
        # If strategy hasn't been generated yet, auto-generate strategy first
        project.strategy = llm_service.generate_strategy(
            topic=project.topic,
            audience=project.audience or "General Audience",
            platform=project.platform or "YouTube Shorts",
            duration=project.duration or 60,
            goal=project.goal or "Educate",
            tone=project.tone or "Educational",
            language=project.language or "English"
        )
        if project.strategy and project.strategy.get("title"):
            project.title = project.strategy["title"]
        
    script_data = llm_service.generate_script(
        topic=project.topic,
        strategy=project.strategy,
        audience=project.audience or "General Audience",
        goal=project.goal or "Educate",
        tone=project.tone or "Educational",
        platform=project.platform or "YouTube Shorts",
        language=project.language or "English"
    )
    
    project.script = script_data
    project.scenes = script_data.get("scenes", [])
    if script_data.get("title") and (not project.title or project.title == "Untitled Project"):
        project.title = script_data["title"]
    project.status = "Ready"
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
def render_video(project_id: int, db: Session = Depends(get_db)):
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
            # Add 0.45s breathing room buffer so voice is NEVER cut off
            audio_dur = video_service.get_audio_duration(audio_path)
            exact_duration = max(audio_dur + 0.45, float(scene.get("duration") or 0), 3.0)
            scene["duration"] = round(exact_duration, 2)

            # 3. Generate Visual with Top Title and Lower-Third Speech Caption
            img_path = image_service.generate_scene_visual(
                description=scene.get("visual_description", "") or narration_text or project.topic,
                title=title_text,
                caption=narration_text,
                aspect_ratio=target_aspect,
                scene_index=idx
            )

            # 4. Render Scene Video
            scene_video_path = video_service.render_scene(
                media_path=img_path,
                audio_path=audio_path,
                duration=exact_duration,
                aspect_ratio=target_aspect
            )
            scene_video_paths.append(scene_video_path)

        # Update scene durations in database
        project.scenes = list(project.scenes)
        db.commit()
            
        # 4. Concatenate
        final_video = video_service.concatenate_scenes(scene_video_paths)
        
        project.output_path = final_video
        project.status = "Completed"

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
        return {"status": "success", "output_path": final_video, "social_post": project.social_post}
        
    except Exception as e:
        print(f"Rendering failed: {e}")
        project.status = "Failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Rendering failed: {str(e)}")


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
        if not os.path.exists(file_path):
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
