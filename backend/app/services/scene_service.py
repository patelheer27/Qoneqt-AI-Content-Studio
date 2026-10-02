from typing import List
from sqlalchemy.orm import Session
from app.models.scene import Scene
from app.schemas.llm import ScenePlanItem

class SceneService:
    @staticmethod
    def create_scenes_from_plan(
        db: Session,
        project_id: str,
        scene_items: List[ScenePlanItem]
    ) -> List[Scene]:
        """
        Creates and persists Scene records in database for a project.
        """
        # Delete any previous scenes if regenerating
        db.query(Scene).filter(Scene.project_id == project_id).delete()
        db.commit()

        scenes = []
        for item in scene_items:
            scene = Scene(
                project_id=project_id,
                scene_number=item.scene_number,
                duration=item.duration,
                narration=item.narration,
                visual_prompt=item.visual_prompt,
                on_screen_text=item.on_screen_text,
                transition=item.transition,
                status="pending"
            )
            db.add(scene)
            scenes.append(scene)

        db.commit()
        for sc in scenes:
            db.refresh(sc)

        return scenes
