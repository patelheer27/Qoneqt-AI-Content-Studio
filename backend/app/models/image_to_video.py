from sqlalchemy import Column, Integer, String, DateTime, JSON, Float
from datetime import datetime
from app.database import Base

class ImageToVideoProject(Base):
    __tablename__ = "image_to_video_projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, default="My Image to Video")
    aspect_ratio = Column(String, default="9:16")
    resolution = Column(String, default="1080p")
    scenes = Column(JSON, default=list)
    settings = Column(JSON, default=dict)
    
    # Status & Rendering Progress
    status = Column(String, default="Draft") # Draft, Rendering, Completed, Failed
    progress = Column(Integer, default=0)
    current_step = Column(String, default="")
    error_message = Column(String, nullable=True)
    
    output_video_path = Column(String, nullable=True)
    output_video_url = Column(String, nullable=True)
    duration = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

