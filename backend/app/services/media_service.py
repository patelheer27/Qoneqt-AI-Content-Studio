import logging
from pathlib import Path
from typing import List
from app.config import settings
from app.models.scene import Scene
from app.utils.image_gen import generate_scene_image

logger = logging.getLogger(__name__)

class MediaService:
    @staticmethod
    def generate_visual_for_scene(
        project_id: str,
        topic: str,
        scene: Scene,
        total_scenes: int
    ) -> Path:
        """
        Generates or renders visual for an individual scene.
        """
        output_filename = f"scene_{project_id}_{scene.scene_number}.png"
        output_path = settings.IMAGES_DIR / output_filename

        # If Image API Key is provided and enabled, could call an external image API here
        # But we ensure high aesthetic quality through the programmatic visual compositor
        try:
            generate_scene_image(
                scene_number=scene.scene_number,
                total_scenes=total_scenes,
                topic=topic,
                on_screen_text=scene.on_screen_text,
                visual_prompt=scene.visual_prompt,
                output_path=output_path,
                width=1080,
                height=1920
            )
            return output_path
        except Exception as e:
            logger.error(f"Failed to generate scene image {scene.scene_number}: {e}")
            raise e

    @classmethod
    def generate_all_scene_visuals(
        cls,
        project_id: str,
        topic: str,
        scenes: List[Scene]
    ) -> List[Path]:
        """
        Generates visuals for all scenes in a project.
        """
        total = len(scenes)
        paths = []
        for sc in scenes:
            path = cls.generate_visual_for_scene(project_id, topic, sc, total)
            sc.visual_path = str(path)
            paths.append(path)
        return paths
