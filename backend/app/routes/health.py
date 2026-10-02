from fastapi import APIRouter
from app.config import settings

router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "Qoneqt AI Content Studio",
        "demo_mode": settings.DEMO_MODE,
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "voice_enabled": settings.VOICE_ENABLED,
        "image_generation_enabled": settings.IMAGE_GENERATION_ENABLED
    }
