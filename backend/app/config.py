import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # SQLite default with robust absolute path
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'video_studio.db').replace(os.sep, '/')}"
    )
    
    DEMO_MODE: str = "false"
    POLLINATIONS_API_KEY: str = os.getenv("POLLINATIONS_API_KEY", "")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
