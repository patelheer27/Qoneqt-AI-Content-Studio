import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.database.session import Base, engine
from app.routes.health import router as health_router
from app.routes.projects import router as projects_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("qoneqt")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database schema on startup
    logger.info("Initializing SQLite database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info(f"Qoneqt Content Studio Backend ready! Demo Mode: {settings.DEMO_MODE}")
    yield
    logger.info("Shutting down Qoneqt Content Studio Backend.")

app = FastAPI(
    title="Qoneqt AI Content Studio API",
    description="End-to-end pipeline: One Idea -> AI Planning -> Script -> Scenes -> Visuals -> Voice -> Captions -> Video Composition -> Publish",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount generated static directory for media assets
app.mount("/generated", StaticFiles(directory=str(settings.GENERATED_DIR)), name="generated")

# Include API Routers
app.include_router(health_router)
app.include_router(projects_router)

# Mount built React frontend if dist exists
dist_dir = settings.ROOT_PATH / "frontend" / "dist"
if dist_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(dist_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        # Don't intercept API or generated routes
        if full_path.startswith("api") or full_path.startswith("generated") or full_path.startswith("docs") or full_path.startswith("openapi"):
            return None
        index_file = dist_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"error": "Frontend build not found"}
else:
    @app.get("/")
    def root():
        return {
            "name": "Qoneqt AI Content Studio",
            "tagline": "From One Idea to a Publish-Ready Video",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/api/health"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
