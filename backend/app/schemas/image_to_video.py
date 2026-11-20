from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

class SceneSchema(BaseModel):
    id: Optional[str] = "scene_default"
    image_url: str
    image_filename: Optional[str] = None
    image_path: Optional[str] = None
    subject: Optional[str] = ""
    width: Optional[int] = 1080
    height: Optional[int] = 1920
    file_size: Optional[int] = 0
    format: Optional[str] = "JPEG"
    text: Optional[str] = ""
    headline: Optional[str] = ""
    duration: Optional[float] = 4.0
    motion_mode: Optional[str] = "camera" # 'camera' or 'ai'
    motion_type: Optional[str] = None      # alias for motion_mode
    camera_motion: Optional[str] = "zoom_in"
    ai_motion_style: Optional[str] = "natural_flow"
    ai_motion: Optional[str] = None        # alias for ai_motion_style
    ai_motion_intensity: Optional[str] = "medium"
    ai_intensity: Optional[str] = None     # alias for ai_motion_intensity
    transition: Optional[str] = "crossfade"
    transition_duration: Optional[float] = 0.8
    audio_url: Optional[str] = None

    class Config:
        extra = "allow"

class SettingsSchema(BaseModel):
    title: Optional[str] = "My Image to Video"
    aspect_ratio: Optional[str] = "16:9"
    resolution: Optional[str] = "1080p"
    voice_enabled: Optional[bool] = True
    voice_id: Optional[str] = "en-US-GuyNeural"
    voice_speed: Optional[str] = "+15%"
    voice_volume: Optional[float] = 1.0
    narration_volume: Optional[float] = None
    custom_voiceover_url: Optional[str] = None
    custom_audio_url: Optional[str] = None
    custom_audio_path: Optional[str] = None
    subtitles_enabled: Optional[bool] = True
    subtitle_enabled: Optional[bool] = None
    subtitle_font: Optional[str] = "Inter"
    subtitle_size: Optional[Union[int, str]] = 32
    subtitle_color: Optional[str] = "#FFFFFF"
    subtitle_bg: Optional[str] = "translucent"
    subtitle_position: Optional[str] = "bottom"
    music_enabled: Optional[bool] = False
    music_track: Optional[str] = "ambient_calm"
    music_id: Optional[str] = None
    music_volume: Optional[float] = 0.2
    custom_music_url: Optional[str] = None

    class Config:
        extra = "allow"

class GenerateRequestSchema(BaseModel):
    title: Optional[str] = "My Image to Video"
    aspect_ratio: Optional[str] = "16:9"
    resolution: Optional[str] = "1080p"
    scenes: List[SceneSchema]
    settings: Optional[SettingsSchema] = None

    class Config:
        extra = "allow"

class PreviewSceneRequestSchema(BaseModel):
    scene: Optional[SceneSchema] = None
    image_url: Optional[str] = None
    motion_type: Optional[str] = None
    motion_mode: Optional[str] = None
    camera_motion: Optional[str] = None
    ai_motion: Optional[str] = None
    ai_motion_style: Optional[str] = None
    ai_intensity: Optional[str] = None
    ai_motion_intensity: Optional[str] = None
    duration: Optional[float] = 4.0
    aspect_ratio: Optional[str] = "16:9"
    resolution: Optional[str] = "720p"
    text: Optional[str] = ""
    headline: Optional[str] = ""
    voice_id: Optional[str] = "en-US-GuyNeural"
    voice_speed: Optional[str] = "+15%"
    voice_enabled: Optional[bool] = True
    subtitles_enabled: Optional[bool] = True
    subtitle_enabled: Optional[bool] = None
    subtitle_font: Optional[str] = "Inter"
    subtitle_size: Optional[Union[int, str]] = 28
    subtitle_color: Optional[str] = "#FFFFFF"
    subtitle_bg: Optional[str] = "translucent"
    subtitle_position: Optional[str] = "bottom"

    class Config:
        extra = "allow"

class JobStatusResponse(BaseModel):
    job_id: int
    status: str
    progress: int
    current_step: str
    error_message: Optional[str] = None
    video_url: Optional[str] = None
    duration: Optional[float] = 0.0

    class Config:
        extra = "allow"

class GenerateScriptRequestSchema(BaseModel):
    topic: Optional[str] = ""
    tone: Optional[str] = "Inspiring"
    scenes_count: int = 5
    images_info: Optional[List[Dict[str, Any]]] = None
    target_duration: Optional[int] = 30

    class Config:
        extra = "allow"

class RewriteSceneRequestSchema(BaseModel):
    scene_index: int = 1
    current_text: Optional[str] = ""
    topic: Optional[str] = ""
    subject: Optional[str] = ""
    tone: Optional[str] = "Inspiring"
    filename: Optional[str] = ""

    class Config:
        extra = "allow"
