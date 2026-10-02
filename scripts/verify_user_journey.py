import urllib.request
import json
import time

def verify_full_journey():
    print("=" * 60)
    print("QONEQT AI CONTENT STUDIO — ACCEPTANCE TEST JOURNEY")
    print("=" * 60)

    # 1. Health check
    print("\n[Step 1] Checking /api/health...")
    with urllib.request.urlopen("http://127.0.0.1:8000/api/health") as res:
        health = json.loads(res.read().decode())
        print(f"-> Health OK: {health['status']}, Voice Enabled: {health['voice_enabled']}")

    # 2. Create Project
    print("\n[Step 2] Creating project with topic: '5 AI trends that will change content creation in 2026'...")
    payload = json.dumps({
        "topic": "5 AI trends that will change content creation in 2026",
        "platform": "Qoneqt Global Feed",
        "duration": 30,
        "tone": "Educational"
    }).encode("utf-8")

    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/projects",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as res:
        project = json.loads(res.read().decode())
        project_id = project["id"]
        print(f"-> Created project ID: {project_id}")

    # 3. Trigger Generation Pipeline
    print("\n[Step 3] Triggering pipeline via POST /api/projects/{id}/generate...")
    gen_req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/projects/{project_id}/generate",
        data=b"{}",
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(gen_req) as res:
        gen_init = json.loads(res.read().decode())
        print(f"-> Pipeline initiated. Initial status: {gen_init['status']}")

    # 4. Poll Status
    print("\n[Step 4] Polling pipeline progress...")
    start_time = time.time()
    last_progress = -1
    final_status = None

    while True:
        time.sleep(1.5)
        with urllib.request.urlopen(f"http://127.0.0.1:8000/api/projects/{project_id}/status") as res:
            status_data = json.loads(res.read().decode())
            cur_prog = status_data["progress"]
            if cur_prog != last_progress:
                print(f"   [+{time.time() - start_time:4.1f}s] Stage: {status_data['stage']:<20} Progress: {cur_prog}%")
                last_progress = cur_prog

            if status_data["status"] in ("ready", "failed"):
                final_status = status_data
                break

    duration = time.time() - start_time
    print(f"-> Pipeline completed in {duration:.1f}s with status: {final_status['status']}")
    assert final_status["status"] == "ready", f"Pipeline failed: {final_status.get('error_message')}"

    # 5. Fetch Full Project Details
    print("\n[Step 5] Fetching complete project details...")
    with urllib.request.urlopen(f"http://127.0.0.1:8000/api/projects/{project_id}") as res:
        full_proj = json.loads(res.read().decode())
        print(f"-> Title: {full_proj['title']}")
        print(f"-> Hook: {full_proj['hook']}")
        print(f"-> Scenes: {len(full_proj['scenes'])}")
        print(f"-> Video URL: {full_proj['video_url']}")
        print(f"-> Hashtags: {full_proj['hashtags']}")

    # 6. Stream and Verify Video MP4
    print("\n[Step 6] Verifying video streaming via GET /api/projects/{id}/video...")
    with urllib.request.urlopen(f"http://127.0.0.1:8000/api/projects/{project_id}/video") as res:
        video_bytes = res.read()
        print(f"-> Video Stream OK! Content-Type: {res.headers.get('Content-Type')}, Size: {len(video_bytes):,} bytes")
        assert len(video_bytes) > 50000, "Video size is too small"

    # 7. Publish to Qoneqt Global Feed
    print("\n[Step 7] Simulating publish to Qoneqt Global Feed...")
    pub_req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/projects/{project_id}/publish",
        data=b"{}",
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(pub_req) as res:
        pub_res = json.loads(res.read().decode())
        print(f"-> Publish status: {pub_res['status']}")
        print(f"-> Message: {pub_res['message']}")
        print(f"-> Published At: {pub_res['published_at']}")

    print("\n" + "=" * 60)
    print("ALL ACCEPTANCE CRITERIA SUCCESSFULLY VERIFIED! [PASS]")
    print("=" * 60)

if __name__ == "__main__":
    verify_full_journey()
