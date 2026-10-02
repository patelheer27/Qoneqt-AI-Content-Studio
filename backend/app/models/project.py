import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from sqlalchemy.orm import relationship
from app.database.session import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    topic = Column(String(500), nullable=False)
    platform = Column(String(100), default="Qoneqt Global Feed")
    duration = Column(Integer, default=30)
    tone = Column(String(50), default="Educational")

    title = Column(String(300), nullable=True)
    hook = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    script = Column(Text, nullable=True)
    caption = Column(Text, nullable=True)
    hashtags = Column(Text, nullable=True)  # JSON encoded list or comma string

    status = Column(String(50), default="created")  # created, planning, generating_assets, generating_voice, generating_captions, composing_video, ready, published, failed
    stage = Column(String(100), default="initialized")
    progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    video_path = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship to scenes
    scenes = relationship("Scene", back_populates="project", cascade="all, delete-orphan", order_by="Scene.scene_number")
