import uuid
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base

class Scene(Base):
    __tablename__ = "scenes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    scene_number = Column(Integer, nullable=False)
    duration = Column(Float, default=5.0)

    narration = Column(Text, nullable=False)
    visual_prompt = Column(Text, nullable=False)
    on_screen_text = Column(String(500), nullable=False)
    transition = Column(String(100), default="fade")

    visual_path = Column(String(500), nullable=True)
    audio_path = Column(String(500), nullable=True)
    caption = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # pending, completed, failed

    project = relationship("Project", back_populates="scenes")
