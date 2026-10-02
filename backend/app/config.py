import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Root directory of the repository (parent of backend)
APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
ROOT_DIR = BACKEND_DIR.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core API Keys
    GEMINI_API_KEY: str = ""
    VOICE_API_KEY: str = ""
    IMAGE_API_KEY: str = ""

    # Database
    DATABASE_URL: str = f"sqlite:///{ROOT_DIR / 'qoneqt.db'}"

    # Pipeline Feature Flags
    VOICE_ENABLED: bool = True
    IMAGE_GENERATION_ENABLED: bool = True
    DEMO_MODE: bool = False

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = ["*"]

    # Storage Paths
    ROOT_PATH: Path = ROOT_DIR
    GENERATED_DIR: Path = ROOT_DIR / "generated"
    IMAGES_DIR: Path = ROOT_DIR / "generated" / "images"
    AUDIO_DIR: Path = ROOT_DIR / "generated" / "audio"
    VIDEOS_DIR: Path = ROOT_DIR / "generated" / "videos"
    CAPTIONS_DIR: Path = ROOT_DIR / "generated" / "captions"

settings = Settings()

# Ensure directories exist
for folder in [
    settings.GENERATED_DIR,
    settings.IMAGES_DIR,
    settings.AUDIO_DIR,
    settings.VIDEOS_DIR,
    settings.CAPTIONS_DIR,
]:
    folder.mkdir(parents=True, exist_ok=True)
