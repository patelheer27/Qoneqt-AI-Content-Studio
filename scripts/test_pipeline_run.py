import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.database.session import Base, engine, SessionLocal
from app.models.project import Project
from app.services.pipeline_service import PipelineService

async def main():
    print(">>> 1. Creating DB tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print(">>> 2. Creating test project...")
    project = Project(
        topic="5 AI trends that will change content creation in 2026",
        platform="Qoneqt Global Feed",
        duration=30,
        tone="Educational",
        status="created"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    p_id = project.id
    db.close()
    print(f"Created project: {p_id}")

    print(">>> 3. Running full video pipeline...")
    await PipelineService.run_pipeline(p_id)

    db = SessionLocal()
    updated = db.query(Project).filter(Project.id == p_id).first()
    print(f"\nPipeline Finished!")
    print(f"Status: {updated.status}")
    print(f"Stage: {updated.stage}")
    print(f"Progress: {updated.progress}%")
    print(f"Title: {updated.title}")
    print(f"Hook: {updated.hook}")
    print(f"Scenes count: {len(updated.scenes)}")
    print(f"Video path: {updated.video_path}")
    if updated.video_path:
        vp = Path(updated.video_path)
        print(f"Video file exists: {vp.exists()} (size: {vp.stat().st_size} bytes)")
    db.close()

if __name__ == "__main__":
    asyncio.run(main())
