# Qoneqt AI Content Studio — LLM Intelligence Architecture

## 1. What LLM is Used and Why

**Model:** Google Gemini 2.5 Flash / Gemini 2.0 Flash (`gemini-2.5-flash`, `gemini-2.0-flash`) via the official `google-genai` SDK.

### Why Gemini?
1. **Native Structured JSON Output:** Gemini supports strict schema enforcement (`response_mime_type="application/json"` and `response_schema`), eliminating malformed responses.
2. **Speed & Latency:** Sub-second latency enables interactive real-time video generation pipelines during live demos.
3. **Multimodal Reasoning:** Exceptional understanding of social pacing, hook psychology, visual composition framing, and timing constraints.
4. **Factual Grounding:** Adheres strictly to factual claims without inventing fake statistics or citations.

---

## 2. Intelligence Layer vs. Media Layer

> **Critical Architectural Principle:**  
> The LLM **does not** generate raw MP4 pixels or waveforms directly.  
> The LLM serves as the **Intelligence and Planning Orchestrator**.  
> Specialized downstream microservices synthesize audio, graphics, captions, and FFmpeg video compositing.

```
+-----------------------------------------------------------+
|                        USER IDEA                          |
|    "5 AI trends that will change content creation in 2026"|
+-----------------------------+-----------------------------+
                              |
                              v
+-----------------------------------------------------------+
|                   GEMINI INTELLIGENCE                     |
|  - Topic Decomposition & Hook Psychology                  |
|  - Structured Scene Planning & Time Budgeting             |
|  - On-Screen Key Copy & Visual Prompts                    |
+-----------------------------+-----------------------------+
                              |
                              v
+-----------------------------------------------------------+
|               PYDANTIC VALIDATION LAYER                   |
|  - Strict validation against ContentPlanSchema            |
|  - Duration rebalancing & scene sanitization              |
+-----------------------------+-----------------------------+
                              |
                              v
+-----------------------------------------------------------+
|               SPECIALIZED MEDIA GENERATION                |
|  - MediaService: 1080x1920 PIL Graphic Composition        |
|  - VoiceService: Neural TTS Speech Synthesis              |
|  - Subtitles: SRT & ASS Timestamped Subtitles             |
+-----------------------------+-----------------------------+
                              |
                              v
+-----------------------------------------------------------+
|                   FFMPEG COMPOSITOR                       |
|  - 9:16 Vertical Video Assembly                           |
|  - H.264 Video + AAC Audio Stream Multiplexing            |
|  - Web-Ready (+faststart) MP4 Delivery                    |
+-----------------------------------------------------------+
```

---

## 3. LLM System Prompt

The exact system prompt configured in `backend/app/services/llm_service.py`:

```text
You are Qoneqt AI Content Planner.

Your job is to transform a user-provided topic into a concise, engaging social-media video plan.

Generate:
* strong title
* attention-grabbing first 2–3 seconds
* concise script
* logical scene structure
* visual descriptions
* narration
* on-screen text
* transitions
* caption
* hashtags

The content must be factual when the topic requires factual claims.
Do not invent sources or statistics.
Keep narration concise enough for the requested duration.
Return ONLY valid JSON matching the provided schema.
The output will be consumed programmatically by the Qoneqt video pipeline.
```

---

## 4. Input & Output Contract

### User Input:
- **Topic:** User's concept (e.g. `"5 AI trends that will change content creation in 2026"`)
- **Platform:** `"Qoneqt Global Feed"`, `"Instagram Reels"`, or `"YouTube Shorts"`
- **Duration:** 20, 30, or 45 seconds
- **Tone:** `"Educational"`, `"News"`, `"Energetic"`, or `"Professional"`

### Pydantic Output Schema:
```json
{
  "title": "string",
  "hook": "string",
  "summary": "string",
  "script": "string",
  "duration_seconds": 30,
  "scenes": [
    {
      "scene_number": 1,
      "duration": 6.0,
      "narration": "string",
      "visual_prompt": "string",
      "on_screen_text": "string",
      "transition": "fade"
    }
  ],
  "caption": "string",
  "hashtags": ["string"]
}
```

---

## 5. How Structured LLM Output Becomes a Video

1. **Plan to Database Entities:**  
   The validated `ContentPlanSchema` creates a `Project` row and relational `Scene` records in SQLite with status `pending`.

2. **Visual Directive Execution:**  
   For each scene, `MediaService` uses `on_screen_text`, `visual_prompt`, and scene metadata to generate a vertical 1080x1920 graphic card with glowing ambient backdrop, category badges, high-contrast typography, and audio waveform aesthetics.

3. **Narration to Audio:**  
   `VoiceService` feeds `scene.narration` to the neural speech synthesis engine, measures precise audio duration with ffprobe, and synchronizes the scene's timeline.

4. **Captions Synchronization:**  
   Exact cumulative offsets are computed from audio tracks to produce synchronized `.srt` and `.ass` subtitle files.

5. **FFmpeg Video Composition:**  
   FFmpeg loops each image with its corresponding audio segment, matches exact frame rates (30 fps), applies vertical scaling/padding (`1080:1920`), and stitches all segments into a unified MP4 (`libx264`, `aac`, `yuv420p`, `+faststart`).

---

## 6. Resilience & Graceful Fallback

If `GEMINI_API_KEY` is not provided, if the API rate limit is exceeded, or if `DEMO_MODE=true`:
- The system automatically triggers `generate_fallback_plan()`.
- It constructs a contextual, high-retention 5-scene plan dynamically tailored to the user's specific topic, duration, and tone.
- **Result:** The studio never crashes, never throws unhandled errors, and always produces a real MP4 video!
