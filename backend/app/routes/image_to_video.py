import os
import re
import threading
import uuid
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models.image_to_video import ImageToVideoProject
from app.schemas.image_to_video import (
    SceneSchema, SettingsSchema, GenerateRequestSchema,
    PreviewSceneRequestSchema, JobStatusResponse,
    GenerateScriptRequestSchema, RewriteSceneRequestSchema
)
from app.services.image_to_video_service import image_to_video_service
from app.services.tts_service import tts_service
from app.services.video_service import video_service

router = APIRouter()

# In-memory progress tracking for responsive real-time UI polling
JOBS_PROGRESS = {}

@router.get("/voices")
def get_voices():
    """Returns available high-definition TTS voices: Female and Male only."""
    return [
        {
            "id": "en-US-JennyNeural",
            "name": "Female (Jenny)",
            "gender": "Female",
            "style": "Warm & Natural",
            "accent": "US",
            "language": "English"
        },
        {
            "id": "en-US-GuyNeural",
            "name": "Male (Guy)",
            "gender": "Male",
            "style": "Professional & Confident",
            "accent": "US",
            "language": "English"
        }
    ]

@router.get("/music-tracks")
def get_music_tracks():
    """Returns background music tracks list (disabled by user configuration)."""
    return []

@router.post("/upload-image")
async def upload_images(files: List[UploadFile] = File(...)):
    """Uploads and validates one or multiple images, extracting dimensions and format."""
    results = []
    errors = []
    
    for f in files:
        try:
            content = await f.read()
            if len(content) > 50 * 1024 * 1024:
                errors.append(f"File '{f.filename}' exceeds 50MB limit.")
                continue
            meta = image_to_video_service.save_uploaded_image(content, f.filename)
            results.append(meta)
        except Exception as e:
            errors.append(f"Failed to process '{f.filename}': {str(e)}")

    if not results and errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    return {
        "success": True,
        "images": results,
        "errors": errors if errors else None
    }

@router.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    """Uploads custom voiceover or background music audio."""
    try:
        content = await file.read()
        if len(content) > 100 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Audio file exceeds 100MB limit.")
        meta = image_to_video_service.save_uploaded_audio(content, file.filename)
        return {
            "success": True,
            "audio": meta
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/generate-script")
def generate_ai_script(req: GenerateScriptRequestSchema):
    """Generates an engaging, cohesive scene-by-scene script using AI from user images/topic."""
    try:
        result = image_to_video_service.generate_script_for_images(
            topic=req.topic or "",
            tone=req.tone or "Inspiring",
            scenes_count=req.scenes_count or 5,
            images_info=req.images_info or []
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate AI script: {str(e)}")

@router.post("/rewrite-scene-script")
def rewrite_single_scene_script(req: RewriteSceneRequestSchema):
    """Rewrites or enhances an individual scene's voiceover narration with AI."""
    try:
        result = image_to_video_service.rewrite_scene_script(
            scene_index=req.scene_index,
            current_text=req.current_text or "",
            topic=req.topic or "",
            tone=req.tone or "Inspiring",
            filename=req.filename or ""
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rewrite scene script: {str(e)}")

@router.post("/preview-scene")
def preview_single_scene(req: PreviewSceneRequestSchema):
    """Renders a fast single-scene preview with motion and subtitles."""
    # Resolve scene properties from nested scene or flat fields
    img_url = req.scene.image_url if req.scene else req.image_url
    if not img_url:
        raise HTTPException(status_code=400, detail="No image URL provided for preview.")

    local_img = image_to_video_service._resolve_local_path(img_url)
    if not os.path.exists(local_img):
        raise HTTPException(status_code=404, detail="Source image file not found.")

    aspect_ratio = req.aspect_ratio or "16:9"
    resolution = req.resolution or "720p"
    w, h = image_to_video_service.get_resolution_dimensions(aspect_ratio, resolution)

    text = (req.scene.text if req.scene else req.text) or ""
    headline = (req.scene.headline if req.scene else req.headline) or ""
    duration = (req.scene.duration if req.scene and req.scene.duration else req.duration) or 4.0
    motion_mode = (req.scene.motion_mode or req.scene.motion_type if req.scene else None) or req.motion_mode or req.motion_type or "camera"
    camera_motion = (req.scene.camera_motion if req.scene else None) or req.camera_motion or "zoom_in"
    ai_motion_style = (req.scene.ai_motion_style or req.scene.ai_motion if req.scene else None) or req.ai_motion_style or req.ai_motion or "natural_flow"
    ai_intensity = (req.scene.ai_motion_intensity or req.scene.ai_intensity if req.scene else None) or req.ai_motion_intensity or req.ai_intensity or "medium"
    
    # Audio generation if voice enabled and text provided
    audio_path = None
    voice_enabled = req.voice_enabled if req.voice_enabled is not None else True
    if voice_enabled and text and text.strip():
        try:
            audio_path = tts_service.generate_voiceover(
                text=text,
                voice_style=req.voice_id or "en-US-GuyNeural",
                rate=req.voice_speed or "+15%"
            )
        except Exception as err:
            print(f"[ImageToVideo] Preview voice error: {err}")

    # If scene has custom audio attached, prefer it
    audio_url = req.scene.audio_url if req.scene else None
    if audio_url:
        custom_a = image_to_video_service._resolve_local_path(audio_url)
        if os.path.exists(custom_a):
            audio_path = custom_a

    subs_enabled = req.subtitles_enabled if req.subtitles_enabled is not None else (req.subtitle_enabled if req.subtitle_enabled is not None else True)
    subtitle_cfg = {
        "subtitles_enabled": subs_enabled,
        "subtitle_font": req.subtitle_font or "Inter",
        "subtitle_size": req.subtitle_size or 28,
        "subtitle_color": req.subtitle_color or "#FFFFFF",
        "subtitle_bg": req.subtitle_bg or "translucent",
        "subtitle_position": req.subtitle_position or "bottom"
    }

    try:
        scene_mp4 = image_to_video_service.render_scene_clip(
            image_path=local_img,
            audio_path=audio_path,
            duration=duration,
            w=w,
            h=h,
            motion_mode=motion_mode,
            camera_motion=camera_motion,
            ai_motion_style=ai_motion_style,
            ai_intensity=ai_intensity,
            headline=headline,
            text=text,
            subtitle_settings=subtitle_cfg,
            aspect_ratio=aspect_ratio
        )
        
        rel_url = f"/storage/renders/{os.path.basename(scene_mp4)}"
        dur = video_service.get_audio_duration(scene_mp4)
        return {
            "success": True,
            "preview_url": rel_url,
            "preview_video_url": rel_url,
            "duration": round(dur, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scene preview failed: {str(e)}")

def _run_video_generation_pipeline(job_id: int, req_data: dict):
    """Background task executing the complete image-to-video compilation pipeline."""
    db = SessionLocal()
    job = db.query(ImageToVideoProject).filter(ImageToVideoProject.id == job_id).first()
    if not job:
        db.close()
        return

    def update_progress(pct: int, step_desc: str):
        JOBS_PROGRESS[job_id] = {"progress": pct, "step": step_desc, "status": "Rendering"}
        try:
            job.progress = pct
            job.current_step = step_desc
            db.commit()
        except Exception:
            pass

    try:
        update_progress(5, "Validating images and settings...")
        scenes = req_data.get("scenes", [])
        settings = req_data.get("settings", {})
        aspect_ratio = req_data.get("aspect_ratio", "9:16")
        resolution = req_data.get("resolution", "1080p")
        
        w, h = image_to_video_service.get_resolution_dimensions(aspect_ratio, resolution)
        
        if not scenes:
            raise ValueError("No images or scenes provided for video generation.")

        # Stage 1: Synthesize voiceovers for scenes
        update_progress(15, "Generating crystal-clear voice narrations...")
        voice_id = settings.get("voice_id", "en-US-GuyNeural")
        voice_speed = settings.get("voice_speed", "+15%")
        voice_enabled = settings.get("voice_enabled", True)

        scene_audio_paths = []
        for idx, sc in enumerate(scenes):
            a_path = None
            if sc.get("audio_url"):
                candidate = image_to_video_service._resolve_local_path(sc["audio_url"])
                if os.path.exists(candidate):
                    a_path = candidate
            elif voice_enabled and sc.get("text") and sc["text"].strip():
                try:
                    a_path = tts_service.generate_voiceover(
                        text=sc["text"],
                        voice_style=voice_id,
                        rate=voice_speed
                    )
                except Exception as tts_err:
                    print(f"[ImageToVideo] Voiceover error for scene {idx+1}: {tts_err}")
            scene_audio_paths.append(a_path)

        # Stage 2: Render animated scene clips
        rendered_scene_clips = []
        transitions = []
        transition_durations = []
        total_scenes = len(scenes)

        subs_enabled = settings.get("subtitles_enabled") if settings.get("subtitles_enabled") is not None else settings.get("subtitle_enabled", True)
        subtitle_cfg = {
            "subtitles_enabled": subs_enabled,
            "subtitle_font": settings.get("subtitle_font", "Inter"),
            "subtitle_size": settings.get("subtitle_size", 32),
            "subtitle_color": settings.get("subtitle_color", "#FFFFFF"),
            "subtitle_bg": settings.get("subtitle_bg", "translucent"),
            "subtitle_position": settings.get("subtitle_position", "bottom")
        }

        for idx, sc in enumerate(scenes):
            pct = 25 + int((idx / total_scenes) * 45)
            s_motion_mode = sc.get("motion_mode") or sc.get("motion_type") or "camera"
            s_camera_motion = sc.get("camera_motion", "zoom_in")
            s_ai_style = sc.get("ai_motion_style") or sc.get("ai_motion") or "natural_flow"
            s_ai_intensity = sc.get("ai_motion_intensity") or sc.get("ai_intensity") or "medium"

            motion_desc = "AI-powered flow" if s_motion_mode == "ai" else s_camera_motion.replace("_", " ").title()
            update_progress(pct, f"Animating Scene {idx + 1}/{total_scenes} ({motion_desc})...")

            local_img = image_to_video_service._resolve_local_path(sc.get("image_url"))
            if not os.path.exists(local_img):
                raise ValueError(f"Image for scene {idx + 1} not found on disk.")

            clip_path = image_to_video_service.render_scene_clip(
                image_path=local_img,
                audio_path=scene_audio_paths[idx],
                duration=float(sc.get("duration", 4.0)),
                w=w,
                h=h,
                motion_mode=s_motion_mode,
                camera_motion=s_camera_motion,
                ai_motion_style=s_ai_style,
                ai_intensity=s_ai_intensity,
                headline=sc.get("headline", ""),
                text=sc.get("text", ""),
                subtitle_settings=subtitle_cfg,
                aspect_ratio=aspect_ratio
            )
            rendered_scene_clips.append(clip_path)
            transitions.append(sc.get("transition", "crossfade"))
            transition_durations.append(float(sc.get("transition_duration", 0.8)))

        # Stage 3: Transitions and Audio Assembly (Background music disabled by configuration)
        update_progress(80, "Applying cinematic transitions & compiling audio...")
        output_filename = f"image_to_video_{job_id}_{uuid.uuid4().hex[:8]}.mp4"
        
        final_mp4 = image_to_video_service.assemble_final_video(
            scene_video_paths=rendered_scene_clips,
            transitions=transitions,
            transition_durations=transition_durations,
            bg_music_path=None,
            bg_music_volume=0.0,
            voice_volume=float(settings.get("voice_volume") if settings.get("voice_volume") is not None else settings.get("narration_volume", 1.0)),
            output_filename=output_filename
        )

        # Stage 5: Finalize
        update_progress(95, "Finalizing professional MP4 video...")
        total_dur = video_service.get_audio_duration(final_mp4)
        video_url = f"/storage/renders/{os.path.basename(final_mp4)}"

        job.status = "Completed"
        job.progress = 100
        job.current_step = "Video ready to preview and download!"
        job.output_video_path = final_mp4
        job.output_video_url = video_url
        job.duration = round(total_dur, 2)
        db.commit()

        JOBS_PROGRESS[job_id] = {
            "progress": 100,
            "step": "Completed",
            "status": "Completed",
            "video_url": video_url,
            "duration": round(total_dur, 2)
        }
        print(f"[ImageToVideo] Job {job_id} successfully compiled: {video_url} ({total_dur:.1f}s)")

    except Exception as e:
        print(f"[ImageToVideo] Job {job_id} failed: {e}")
        JOBS_PROGRESS[job_id] = {
            "progress": 0,
            "step": "Failed",
            "status": "Failed",
            "error_message": str(e)
        }
        try:
            job.status = "Failed"
            job.error_message = str(e)
            db.commit()
        except Exception:
            pass
    finally:
        db.close()

@router.post("/generate", response_model=JobStatusResponse)
def generate_image_to_video(req: GenerateRequestSchema, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Starts asynchronous full video generation from scenes and configuration."""
    if not req.scenes:
        raise HTTPException(status_code=400, detail="Please upload at least one image to generate a video.")

    # Create job in database
    job = ImageToVideoProject(
        title=req.title or "My Image to Video",
        aspect_ratio=req.aspect_ratio,
        resolution=req.resolution,
        scenes=[s.model_dump() for s in req.scenes],
        settings=req.settings.model_dump(),
        status="Rendering",
        progress=5,
        current_step="Queued for video rendering..."
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Launch background thread
    t = threading.Thread(
        target=_run_video_generation_pipeline,
        args=(job.id, req.model_dump()),
        daemon=True
    )
    t.start()

    return JobStatusResponse(
        job_id=job.id,
        status="Rendering",
        progress=5,
        current_step="Queued for video rendering..."
    )

@router.get("/status/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """Polls real-time video generation progress."""
    cached = JOBS_PROGRESS.get(job_id)
    if cached:
        return JobStatusResponse(
            job_id=job_id,
            status=cached.get("status", "Rendering"),
            progress=cached.get("progress", 0),
            current_step=cached.get("step", ""),
            error_message=cached.get("error_message"),
            video_url=cached.get("video_url"),
            duration=cached.get("duration", 0.0)
        )

    job = db.query(ImageToVideoProject).filter(ImageToVideoProject.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        current_step=job.current_step,
        error_message=job.error_message,
        video_url=job.output_video_url,
        duration=job.duration
    )

@router.get("/projects")
def get_recent_projects(db: Session = Depends(get_db)):
    """Returns list of recent Image-to-Video projects."""
    projects = (
        db.query(ImageToVideoProject)
        .order_by(ImageToVideoProject.created_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": p.id,
            "title": p.title,
            "status": p.status,
            "progress": p.progress,
            "duration": p.duration,
            "video_url": p.output_video_url,
            "scenes_count": len(p.scenes) if p.scenes else 0,
            "created_at": p.created_at.isoformat() if p.created_at else None
        }
        for p in projects
    ]

@router.get("/download/{project_id}")
def download_project_video(project_id: int, db: Session = Depends(get_db)):
    """Serves the generated video as a direct browser attachment download."""
    job = db.query(ImageToVideoProject).filter(ImageToVideoProject.id == project_id).first()
    if not job or not job.output_video_path or not os.path.exists(job.output_video_path):
        raise HTTPException(status_code=404, detail="Generated video file not found.")

    clean_title = re.sub(r'[^a-zA-Z0-9_-]', '_', job.title.strip()) or "image_to_video"
    filename = f"{clean_title}.mp4"
    return FileResponse(
        path=job.output_video_path,
        media_type="video/mp4",
        filename=filename
    )
