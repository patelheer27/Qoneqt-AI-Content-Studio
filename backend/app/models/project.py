from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from datetime import datetime
from app.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, default="Untitled Project")
    topic = Column(String, nullable=False)
    audience = Column(String, default="General Audience")
    goal = Column(String, default="Educate")
    platform = Column(String, default="YouTube Shorts")
    aspect_ratio = Column(String, default="9:16")
    duration = Column(Integer, default=60)
    tone = Column(String, default="Professional")
    language = Column(String, default="English")
    
    # Store AI generated content
    strategy = Column(JSON, nullable=True) # AI Director output
    script = Column(JSON, nullable=True)   # Structured script
    scenes = Column(JSON, nullable=True)   # Storyboard scenes
    social_post = Column(JSON, nullable=True) # Captions & Hashtags for posting
    
    # Settings
    voice_settings = Column(JSON, nullable=True)
    caption_settings = Column(JSON, nullable=True)
    
    # Status
    status = Column(String, default="Draft") # Draft, Planning, Ready, Rendering, Completed, Failed
    output_path = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
