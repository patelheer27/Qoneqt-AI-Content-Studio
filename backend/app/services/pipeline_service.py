import json
import logging
import asyncio
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.config import settings
from app.database.session import SessionLocal
from app.models.project import Project
from app.models.scene import Scene
from app.services.llm_service import generate_content_plan
from app.services.scene_service import SceneService
from app.services.media_service import MediaService
from app.services.voice_service import VoiceService
from app.services.video_service import VideoService

logger = logging.getLogger(__name__)

class PipelineService:
    @staticmethod
    def _update_progress(db: Session, project: Project, stage: str, progress: int, status: str = "processing"):
        project.stage = stage
        project.progress = progress
        project.status = status
        project.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(project)

    @classmethod
    async def run_pipeline(cls, project_id: str):
        """
        Executes the full end-to-end AI video creation pipeline asynchronously:
        Input -> AI Planning -> Script -> Scene Plan -> Visuals -> Voice -> Captions -> Composition -> Ready
        """
        db = SessionLocal()
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                logger.error(f"Project {project_id} not found for pipeline.")
                return

            logger.info(f"Starting pipeline for project {project_id}: '{project.topic}'")

            # 1. Analyze Topic
            cls._update_progress(db, project, stage="analyzing_topic", progress=10, status="processing")
            await asyncio.sleep(0.5)

            # 2. AI Planning & Structured Script Generation
            cls._update_progress(db, project, stage="ai_planning", progress=25, status="processing")
            plan = generate_content_plan(
                topic=project.topic,
                tone=project.tone or "Educational",
                duration=project.duration or 30,
                platform=project.platform or "Qoneqt Global Feed"
            )

            project.title = plan.title
            project.hook = plan.hook
            project.summary = plan.summary
            project.script = plan.script
            project.caption = plan.caption
            project.hashtags = json.dumps(plan.hashtags)
            db.commit()

            # Create scenes in DB
            scenes = SceneService.create_scenes_from_plan(db, project.id, plan.scenes)
            cls._update_progress(db, project, stage="content_generated", progress=40, status="processing")
            await asyncio.sleep(0.4)

            # 3. Generate Scene Visuals
            cls._update_progress(db, project, stage="generating_visuals", progress=55, status="processing")
            MediaService.generate_all_scene_visuals(project.id, project.topic, scenes)
            for sc in scenes:
                sc.status = "visual_ready"
            db.commit()
            await asyncio.sleep(0.4)

            # 4. Generate Voice Narration
            cls._update_progress(db, project, stage="generating_voice", progress=72, status="processing")
            await VoiceService.generate_all_scene_audio(project.id, scenes)
            for sc in scenes:
                sc.status = "audio_ready"
            db.commit()
            await asyncio.sleep(0.4)

            # 5. Generate Captions & Subtitles
            cls._update_progress(db, project, stage="generating_captions", progress=82, status="processing")
            await asyncio.sleep(0.3)

            # 6. Video Composition with FFmpeg
            cls._update_progress(db, project, stage="composing_video", progress=90, status="processing")
            final_mp4, srt_path = VideoService.compose_full_video(project.id, scenes)

            # 7. Finalize & Save
            project.video_path = str(final_mp4)
            for sc in scenes:
                sc.status = "completed"
            cls._update_progress(db, project, stage="completed", progress=100, status="ready")

            logger.info(f"Pipeline completed successfully for {project_id}! MP4: {final_mp4}")

        except Exception as e:
            logger.exception(f"Pipeline failed for project {project_id}: {e}")
            try:
                project = db.query(Project).filter(Project.id == project_id).first()
                if project:
                    project.status = "failed"
                    project.stage = "error"
                    project.error_message = str(e)
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()
