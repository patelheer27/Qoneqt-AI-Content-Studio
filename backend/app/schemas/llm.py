from typing import List, Optional
from pydantic import BaseModel, Field

class ScenePlanItem(BaseModel):
    scene_number: int = Field(..., description="Sequential scene number starting at 1")
    duration: float = Field(..., description="Duration in seconds for this scene")
    narration: str = Field(..., description="Spoken narration text for this scene")
    visual_prompt: str = Field(..., description="Detailed description of visual layout, background, and imagery")
    on_screen_text: str = Field(..., description="Punchy key headline or bullet shown on screen")
    transition: str = Field(default="fade", description="Transition style to the next scene (fade, zoom, slide)")

class ContentPlanSchema(BaseModel):
    title: str = Field(..., description="Catchy content title for the social video")
    hook: str = Field(..., description="Attention-grabbing opening hook for the first 2-3 seconds")
    summary: str = Field(..., description="Short summary of the video narrative")
    script: str = Field(..., description="Full combined script across all scenes")
    duration_seconds: int = Field(default=30, description="Total target duration in seconds")
    scenes: List[ScenePlanItem] = Field(..., min_length=1, description="List of structured scenes")
    caption: str = Field(..., description="Post caption ready for social platforms")
    hashtags: List[str] = Field(default_factory=list, description="Relevant hashtags for distribution")
