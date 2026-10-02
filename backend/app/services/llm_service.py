import json
import logging
import re
from typing import Optional
from app.config import settings
from app.schemas.llm import ContentPlanSchema, ScenePlanItem

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Qoneqt AI Content Planner.

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
"""

def generate_fallback_plan(topic: str, tone: str = "Educational", duration: int = 30, platform: str = "Qoneqt Global Feed") -> ContentPlanSchema:
    """
    Generates a realistic, structured content plan if the external LLM is offline,
    unconfigured, rate-limited, or in DEMO_MODE.
    """
    clean_topic = topic.strip()
    words = clean_topic.split()
    target_duration = max(20, min(60, duration))

    # Divide into 4 or 5 scenes
    num_scenes = 5 if target_duration >= 30 else 4
    scene_duration = round(target_duration / num_scenes, 1)

    title = f"{clean_topic.title()} | Qoneqt Breakdown"
    hook = f"Did you know {clean_topic} is completely reshaping content creation right now?"
    
    scenes = [
        ScenePlanItem(
            scene_number=1,
            duration=scene_duration,
            narration=f"Here is what you need to know about {clean_topic}.",
            visual_prompt=f"Bold high-tech intro screen showcasing {clean_topic} with pulsing neon holographic grids and sleek data particles.",
            on_screen_text=f"The Truth About {clean_topic[:35]}",
            transition="fade"
        ),
        ScenePlanItem(
            scene_number=2,
            duration=scene_duration,
            narration="First: autonomous intelligence is turning individual creators into full media production studios.",
            visual_prompt="Multi-agent AI network visualizing simultaneous scriptwriting, graphic generation, and voice synthesis.",
            on_screen_text="1. Autonomous Media Pipelines",
            transition="slide"
        ),
        ScenePlanItem(
            scene_number=3,
            duration=scene_duration,
            narration="Second: real-time multimodal composition builds audio, visuals, and captions synchronously in seconds.",
            visual_prompt="Sleek glassmorphism audio-visual timeline rendering video clips with automated dynamic subtitles.",
            on_screen_text="2. Real-Time Multimodal Sync",
            transition="zoom"
        ),
        ScenePlanItem(
            scene_number=4,
            duration=scene_duration,
            narration="Third: frictionless distribution gets your content publish-ready across global feeds instantly.",
            visual_prompt="Global social feed visualization with instant engagement metrics and live publishing network.",
            on_screen_text="3. Instant Global Distribution",
            transition="slide"
        ),
    ]

    if num_scenes == 5:
        scenes.append(
            ScenePlanItem(
                scene_number=5,
                duration=scene_duration,
                narration="Stay ahead of the curve. Build your next idea with Qoneqt AI Content Studio.",
                visual_prompt="Modern glowing call to action banner featuring Qoneqt AI Content Studio logo and animated follow prompt.",
                on_screen_text="Build It With Qoneqt AI",
                transition="fade"
            )
        )

    full_script = " ".join([s.narration for s in scenes])
    tag_seeds = [re.sub(r'[^a-zA-Z0-9]', '', w.lower()) for w in words if len(w) > 3][:4]
    hashtags = [f"#{t}" for t in tag_seeds if t] + ["#AIContent", "#Qoneqt", "#FutureTech"]

    return ContentPlanSchema(
        title=title,
        hook=hook,
        summary=f"A fast-paced, high-retention breakdown of {clean_topic} designed for {platform}.",
        script=full_script,
        duration_seconds=target_duration,
        scenes=scenes,
        caption=f"{hook}\n\nExplore how modern AI transforms one idea into publish-ready video.\n\n{' '.join(hashtags)}",
        hashtags=hashtags
    )

def extract_json_from_response(text: str) -> str:
    """Strips markdown code fences and isolates JSON content"""
    text = text.strip()
    # Match ```json ... ``` or ``` ... ```
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if match:
        return match.group(1).strip()
    return text

def generate_content_plan(
    topic: str,
    tone: str = "Educational",
    duration: int = 30,
    platform: str = "Qoneqt Global Feed"
) -> ContentPlanSchema:
    """
    Calls Gemini API to generate structured content plan, with graceful fallback.
    """
    if settings.DEMO_MODE or not settings.GEMINI_API_KEY:
        logger.info("Using Fallback / Demo Mode for content plan generation.")
        return generate_fallback_plan(topic, tone, duration, platform)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        user_prompt = f"""Generate a structured social video plan for:
Topic: "{topic}"
Tone: {tone}
Target Duration: {duration} seconds
Target Platform: {platform}

Ensure the output adheres exactly to the required JSON schema with {duration // 6 or 4} to 5 scenes.
Format response strictly as valid JSON."""

        # Attempt structured output generation using Gemini
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=ContentPlanSchema,
                    temperature=0.7,
                )
            )
            raw_text = response.text
            parsed = ContentPlanSchema.model_validate_json(raw_text)
            return parsed
        except Exception as e_structured:
            logger.warning(f"Structured schema call failed, falling back to standard prompt: {e_structured}")
            # Fallback to standard prompt requesting JSON
            schema_sample = ContentPlanSchema.model_json_schema()
            fallback_prompt = f"{user_prompt}\n\nJSON Schema:\n{json.dumps(schema_sample)}\n\nRespond with valid JSON only."
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=fallback_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.7
                )
            )
            cleaned = extract_json_from_response(response.text)
            parsed = ContentPlanSchema.model_validate_json(cleaned)
            return parsed

    except Exception as e:
        logger.error(f"Gemini API generation failed: {e}. Falling back to deterministic planner.")
        return generate_fallback_plan(topic, tone, duration, platform)
