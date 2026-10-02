from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.llm import ScenePlanItem

class ProjectCreate(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500, description="User provided topic or idea")
    platform: Optional[str] = Field("Qoneqt Global Feed", description="Target platform")
    duration: Optional[int] = Field(30, description="Target duration in seconds")
    tone: Optional[str] = Field("Educational", description="Tone of video")

class SceneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    scene_number: int
    duration: float
    narration: str
    visual_prompt: str
    on_screen_text: str
    transition: str
    visual_path: Optional[str] = None
    audio_path: Optional[str] = None
    caption: Optional[str] = None
    status: str

class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    topic: str
    platform: str
    duration: int
    tone: str
    title: Optional[str] = None
    hook: Optional[str] = None
    summary: Optional[str] = None
    script: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    status: str
    stage: str
    progress: int
    error_message: Optional[str] = None
    video_path: Optional[str] = None
    video_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    scenes: List[SceneResponse] = []

class ProjectStatusResponse(BaseModel):
    project_id: str
    status: str
    stage: str
    progress: int
    error_message: Optional[str] = None
    video_url: Optional[str] = None

class PublishResponse(BaseModel):
    project_id: str
    title: str
    status: str
    platform: str
    published_at: datetime
    video_url: str
    message: str
