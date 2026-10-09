from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ProjectBase(BaseModel):
    topic: str
    audience: Optional[str] = "General Audience"
    goal: Optional[str] = "Educate"
    platform: Optional[str] = "YouTube Shorts"
    aspect_ratio: Optional[str] = "9:16"
    duration: Optional[int] = 60
    tone: Optional[str] = "Professional"
    language: Optional[str] = "English"

class ProjectCreate(ProjectBase):
    pass

class SceneSchema(BaseModel):
    scene_id: int
    duration: float
    narration: str
    visual_description: str
    on_screen_text: str
    transition: str

class StrategySchema(BaseModel):
    title: str
    hook: str
    recommended_duration: int
    style: str
    scenes_count: int
    voice_style: str
    caption_style: str
    cta: str

class ProjectResponse(ProjectBase):
    id: int
    title: str
    status: str
    output_path: Optional[str] = None
    strategy: Optional[Dict[str, Any]] = None
    script: Optional[Dict[str, Any]] = None
    scenes: Optional[List[Dict[str, Any]]] = None
    social_post: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
