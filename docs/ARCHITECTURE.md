# Qoneqt AI Content Studio — System Architecture

## 1. High-Level System Architecture

The following diagram illustrates the complete end-to-end architecture:

```mermaid
flowchart TD
    User([User / Creator]) -->|Enters Idea & Config| ReactApp["React 18 + Vite Frontend"]
    
    subgraph Frontend ["Client Layer (Port 5173 / Production SPA)"]
        ReactApp --> Dashboard["Dashboard & Hero View"]
        ReactApp --> PipelineUI["Live Pipeline Tracker"]
        ReactApp --> VideoPlayer["HTML5 Video Player"]
        ReactApp --> ProjectHistory["Projects History"]
    end

    ReactApp -->|REST API Requests & Polling| FastAPIServer["FastAPI Backend (Port 8000)"]

    subgraph Backend ["FastAPI Application Services"]
        FastAPIServer --> ProjectRouter["/api/projects Router"]
        FastAPIServer --> HealthRouter["/api/health Router"]
        ProjectRouter --> PipelineSvc["PipelineService Orchestrator"]
        
        PipelineSvc --> LLMSvc["LLM Service (Gemini API / Fallback)"]
        PipelineSvc --> SceneSvc["SceneService"]
        PipelineSvc --> MediaSvc["MediaService (1080x1920 PIL Compositor)"]
        PipelineSvc --> VoiceSvc["VoiceService (Neural TTS / Fallback)"]
        PipelineSvc --> VideoSvc["VideoService (FFmpeg Compositor)"]
    end

    subgraph DataStorage ["Persistence & Artifact Layer"]
        ProjectRouter <--> SQLite[("SQLite Database: qoneqt.db")]
        SceneSvc <--> SQLite
        MediaSvc --> ImgStore[("generated/images/")]
        VoiceSvc --> AudioStore[("generated/audio/")]
        VideoSvc --> CaptionsStore[("generated/captions/")]
        VideoSvc --> VideoStore[("generated/videos/")]
    end

    VideoStore -->|Video Streaming / Range Requests| FastAPIServer
```

---

## 2. End-to-End Pipeline Execution Flow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Frontend as React Frontend
    participant API as FastAPI Backend
    participant DB as SQLite DB
    participant LLM as Gemini LLM
    participant Media as MediaService (PIL)
    participant Voice as VoiceService (TTS)
    participant Video as VideoService (FFmpeg)

    User->>Frontend: Enter topic "5 AI trends in 2026" & Click "Generate Video"
    Frontend->>API: POST /api/projects
    API->>DB: Insert Project (status="created")
    API-->>Frontend: Return ProjectResponse (ID)
    Frontend->>API: POST /api/projects/{id}/generate
    API-->>Frontend: Return 200 (status="processing", stage="analyzing_topic")
    
    par Background Pipeline Execution
        API->>LLM: generate_content_plan(topic, tone, duration, platform)
        LLM-->>API: ContentPlanSchema (Structured JSON)
        API->>DB: Update Project (title, hook, script) & Insert Scenes
        API->>Media: generate_all_scene_visuals(scenes)
        Media-->>API: Save 1080x1920 PNG cards to generated/images/
        API->>Voice: generate_all_scene_audio(scenes)
        Voice-->>API: Save MP3 speech tracks & measure durations
        API->>Video: compose_full_video(scenes)
        Note over Video: FFmpeg joins clips into 9:16 vertical MP4
        Video-->>API: Output final MP4 & captions (SRT/ASS)
        API->>DB: Update Project (status="ready", progress=100)
    and Frontend Polling
        loop Every 1.5s
            Frontend->>API: GET /api/projects/{id}/status
            API-->>Frontend: Return progress %, current stage
        end
    end

    Frontend->>API: GET /api/projects/{id}
    API-->>Frontend: Return full project with scenes & video URL
    Frontend->>User: Display Video Preview, Script, Scenes & Enable Publish
    User->>Frontend: Click "Publish to Qoneqt Global Feed"
    Frontend->>API: POST /api/projects/{id}/publish
    API->>DB: Update Project (status="published")
    API-->>Frontend: Return Publish confirmation
```

---

## 3. Database Entity-Relationship Diagram

```mermaid
erDiagram
    PROJECTS ||--o{ SCENES : contains
    PROJECTS {
        string id PK "UUID"
        string topic "User concept"
        string platform "Target social platform"
        int duration "Target duration in seconds"
        string tone "Tone style"
        string title "Catchy content title"
        text hook "Attention hook (0-3s)"
        text summary "Narrative summary"
        text script "Full script narration"
        text caption "Ready-to-post caption"
        text hashtags "JSON list of tags"
        string status "created | processing | ready | published | failed"
        string stage "Current active pipeline stage"
        int progress "Progress 0-100"
        text error_message "Nullable error"
        string video_path "Local filesystem path to MP4"
        datetime created_at
        datetime updated_at
    }

    SCENES {
        string id PK "UUID"
        string project_id FK "References projects.id"
        int scene_number "Index 1 to N"
        float duration "Scene duration in seconds"
        text narration "Spoken voiceover text"
        text visual_prompt "Detailed visual directive"
        string on_screen_text "Key headline on screen"
        string transition "fade | slide | zoom"
        string visual_path "Path to generated 1080x1920 PNG"
        string audio_path "Path to generated narration MP3"
        text caption "Scene caption"
        string status "pending | visual_ready | audio_ready | completed"
    }
```

---

## 4. Pipeline State Transition Diagram

```mermaid
stateDiagram-v2
    [*] --> Initialized: POST /api/projects
    Initialized --> AnalyzingTopic: POST /api/projects/{id}/generate (progress=10%)
    AnalyzingTopic --> AIPlanning: Query Gemini (progress=25%)
    AIPlanning --> ScenesPersisted: Validate ContentPlanSchema (progress=40%)
    ScenesPersisted --> GeneratingVisuals: Render 1080x1920 PIL Cards (progress=55%)
    GeneratingVisuals --> GeneratingVoice: Synthesize Neural Audio (progress=72%)
    GeneratingVoice --> GeneratingCaptions: Create SRT/ASS Subtitles (progress=82%)
    GeneratingCaptions --> ComposingVideo: FFmpeg H.264 / AAC 9:16 Encode (progress=90%)
    ComposingVideo --> Ready: Video Finalized (progress=100%)
    Ready --> Published: POST /api/projects/{id}/publish
    
    AnalyzingTopic --> Failed: Exception caught
    AIPlanning --> Failed: Exception caught
    GeneratingVisuals --> Failed: Exception caught
    GeneratingVoice --> Failed: Exception caught
    ComposingVideo --> Failed: Exception caught
```
