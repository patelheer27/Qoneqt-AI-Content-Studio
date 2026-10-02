# QONEQT AI CONTENT STUDIO

> **From One Idea to a Publish-Ready Video.**

Qoneqt AI Content Studio is a full-stack, automated video production pipeline that transforms a single topic or content concept into an attention-grabbing, publish-ready 9:16 vertical social video (1080x1920 MP4).

---

## 1. Problem & Solution

### The Problem
Solo creators and social media teams spend 4–8 hours researching topics, writing hooks, scripting scene-by-scene timing, designing visual graphics, recording narration, timing subtitles, and compositing clips in video editors for short-form platforms (Qoneqt, Reels, Shorts).

### The Qoneqt Solution
Enter a single prompt (e.g., *"5 AI trends that will change content creation in 2026"*). In under 60 seconds, Qoneqt autonomously executes the entire pipeline:
```
Input → AI Planning → Script → Scene Plan → Visuals → Voice → Captions → Video Composition → Preview → Publish
```

---

## 2. Key Features

- **⚡ Instant End-to-End Execution:** No fake UI or mocked buttons — generates real H.264/AAC MP4 files viewable in any modern browser.
- **🧠 Gemini 2.5 Intelligence:** High-precision structured planning using Pydantic schema validation for titles, hooks, narration, on-screen text, transitions, and hashtags.
- **🎨 1080x1920 Vertical Visual Engine:** High-contrast, glassmorphism cards rendered at 1080x1920 with scene-specific gradients, glowing accents, category badges, and dynamic waveforms.
- **🎙️ Neural Speech Synthesis:** Ultra-realistic, human-sounding voiceover narration with automatic audio duration synchronization.
- **📝 Synchronized Captions:** Generates timestamped `.srt` and `.ass` subtitles for social platforms.
- **🎬 FFmpeg Video Compositor:** Concurrently stitches audio and visuals with Web-optimized `+faststart` metadata for instant browser streaming.
- **📱 Simulated Social Publishing:** 1-click publishing workflow to the Qoneqt Global Feed with simulated feed card and engagement metadata.
- **📂 Project History & Management:** Persistent SQLite storage with instant preview, playback, and MP4 download.
- **🛡️ 100% Offline / Graceful Demo Mode:** Operates reliably even without external API keys or when offline.

---

## 3. Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, Vite 6, Tailwind CSS 3.4, Lucide Icons |
| **Backend** | Python 3.11+, FastAPI, Uvicorn, SQLAlchemy, Pydantic v2 |
| **AI Intelligence** | Google Gemini 2.5 Flash (`google-genai` SDK) |
| **Media Generation** | Pillow (PIL 1080x1920 Engine), edge-tts / gTTS |
| **Video Compositor** | FFmpeg 7.1 (H.264 video, AAC audio, 9:16 1080x1920) |
| **Database** | SQLite (`qoneqt.db`) |
| **Containerization** | Docker, Docker Compose |

---

## 4. Project Structure

```
qoneqt-ai-content-studio/
├── frontend/                     # React 18 + Vite + Tailwind CSS
│   ├── src/
│   │   ├── components/           # Header, ArchitectureBar, PipelineTracker,
│   │   │                         # VideoPreviewCard, ContentPlanView, PublishModal
│   │   ├── pages/                # Dashboard, ProjectsHistory
│   │   ├── services/             # api.js client
│   │   ├── App.jsx               # Main state & polling orchestration
│   │   ├── main.jsx              # React DOM mounting
│   │   └── index.css             # Tailwind base & custom styles
│   ├── package.json
│   ├── vite.config.js            # Reverse proxy for /api and /generated
│   └── tailwind.config.js
│
├── backend/                      # Python FastAPI application
│   └── app/
│       ├── main.py               # Application factory & SPA mounting
│       ├── config.py             # Environment configuration (Pydantic Settings)
│       ├── database/             # SQLite session & engine
│       ├── models/               # SQLAlchemy models (Project, Scene)
│       ├── schemas/              # Pydantic v2 validation schemas
│       ├── routes/               # API routers (/api/health, /api/projects)
│       ├── services/             # LLM, media, voice, video, pipeline services
│       └── utils/                # Subtitle formatter, Pillow image compositor
│
├── generated/                    # Output directory for pipeline assets
│   ├── images/                   # 1080x1920 scene graphics
│   ├── audio/                    # Synthesized narration MP3s
│   ├── videos/                   # Final composited MP4 videos
│   └── captions/                 # SRT & ASS caption files
│
├── docs/                         # Comprehensive documentation
│   ├── LLM.md                    # Detailed LLM architecture & prompt design
│   └── ARCHITECTURE.md           # System design & Mermaid diagrams
│
├── scripts/                      # Helper scripts
│   └── test_pipeline_run.py      # Headless test runner
│
├── tests/                        # Automated backend test suite (pytest)
│   ├── test_api.py
│   └── test_pipeline.py
│
├── .env.example                  # Environment configuration template
├── requirements.txt              # Backend Python dependencies
├── package.json                  # Root npm runner scripts
├── Dockerfile                    # Multi-stage production container
├── docker-compose.yml            # Container deployment configuration
└── README.md
```

---

## 5. Quick Start (Local Development)

### Prerequisites
- **Python 3.10+** (Python 3.11, 3.12, 3.14 supported)
- **Node.js 18+** & npm
- **FFmpeg** (automatically detected from system PATH or bundled via `imageio-ffmpeg`)

---

### Step 1: Clone & Configure Environment

```bash
# Clone the repository
git clone https://github.com/your-username/qoneqt-ai-content-studio.git
cd qoneqt-ai-content-studio

# Copy environment variables
cp .env.example .env
```

Edit `.env` to supply your **Google Gemini API Key**:
```env
GEMINI_API_KEY=your_gemini_api_key_here
VOICE_ENABLED=true
IMAGE_GENERATION_ENABLED=true
DEMO_MODE=false
```
*(If no API key is provided, the application automatically runs in robust Demo Mode!)*

---

### Step 2: Backend Setup & Launch

```bash
# Optional: Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install Python requirements
pip install -r requirements.txt

# Run the FastAPI server
uvicorn app.main:app --app-dir backend --reload --port 8000
```
Backend will be live at: **`http://localhost:8000`**  
Interactive API Docs (Swagger): **`http://localhost:8000/docs`**

---

### Step 3: Frontend Setup & Launch

In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
Frontend will be live at: **`http://localhost:5173`**

---

## 6. Demo Mode (Zero-Config Hackathon Presentation)

To demonstrate the full application without external API calls or network dependencies:
1. In `.env`, set:
   ```env
   DEMO_MODE=true
   ```
2. In the dashboard, click the preset button:
   > **✨ Use Demo Topic: "5 AI trends that will change content creation in 2026"**
3. Click **Generate Video**.
4. The system will run the entire pipeline deterministically in ~25 seconds, producing:
   - Full 5-scene content blueprint
   - 1080x1920 visuals
   - Spoken audio narration
   - SRT subtitles
   - Playable 9:16 vertical MP4 video ready to publish!

---

## 7. Running Backend Tests

Run the automated test suite verifying health, project creation, schema validation, and video publishing:

```bash
pytest tests/
```

Expected output:
```
tests/test_api.py .....                                      [ 71%]
tests/test_pipeline.py ..                                    [100%]
======================== 7 passed in 2.86s ========================
```

---

## 8. Docker Deployment

Deploy the entire full-stack application as a single self-contained container:

```bash
# Build and run with Docker Compose
docker-compose up --build
```
Access the application at: **`http://localhost:8000`**

---

## 9. API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check & engine status |
| `POST` | `/api/projects` | Create a new project record |
| `POST` | `/api/projects/{id}/generate` | Trigger asynchronous video pipeline |
| `GET` | `/api/projects/{id}` | Get full project details & scenes |
| `GET` | `/api/projects/{id}/status` | Poll pipeline progress & stage |
| `GET` | `/api/projects/{id}/video` | Stream or download generated MP4 |
| `GET` | `/api/projects` | List all previous projects |
| `POST` | `/api/projects/{id}/publish` | Simulate publishing to Qoneqt Global Feed |

---

## 10. Future Roadmap

1. **Direct Social API Integrations:** OAuth publishing to Instagram Reels, TikTok, and YouTube Shorts.
2. **AI Avatar Lip-Sync:** Integrate SadTalker or Wav2Lip for talking human avatars.
3. **Multi-Track BGM Audio Ducking:** Automatic volume ducking of background music during speech narration.
4. **Custom Brand Kits:** Upload custom brand color palettes, fonts, and watermarks.

---

## 11. License

MIT License. Built for the Qoneqt AI Hackathon.
