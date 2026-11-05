import json
import os
import re
import html
import time
import requests
import urllib.parse
from groq import Groq
from app.config import settings

class LLMService:
    def __init__(self):
        self.api_key = getattr(settings, "GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
        self.model = getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile") or "llama-3.3-70b-versatile"
        self.pollinations_api_key = getattr(settings, "POLLINATIONS_API_KEY", "") or os.getenv("POLLINATIONS_API_KEY", "")
        self.last_pollinations_time = 0.0
        self._cached_scripts = {}
        
        # Sanitize model name if it contains invalid identifiers
        if not self.model or "gpt-oss" in self.model or self.model.startswith("openai/"):
            self.model = "llama-3.3-70b-versatile"
            
        self.client = None
        if self.api_key and self.api_key.strip():
            try:
                self.client = Groq(api_key=self.api_key.strip())
            except Exception as e:
                print(f"[LLMService] Error initializing Groq client: {e}")
                self.client = None

    def _extract_json(self, text: str) -> dict:
        """Extracts and parses JSON from text, handling reasoning tags and markdown codeblocks."""
        clean = text.strip()
        # Strip reasoning models' think blocks
        clean = re.sub(r'<think>[\s\S]*?</think>', '', clean, flags=re.IGNORECASE).strip()
        if "```" in clean:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean, re.IGNORECASE)
            if match:
                clean = match.group(1).strip()
        first = clean.find("{")
        last = clean.rfind("}")
        if first != -1 and last != -1:
            clean = clean[first:last + 1]
        try:
            return json.loads(clean)
        except Exception:
            # Handle possible trailing commas before closing braces
            clean_fixed = re.sub(r',\s*([}\]])', r'\1', clean)
            return json.loads(clean_fixed)

    def _call_groq_json(self, system_prompt: str, user_prompt: str) -> dict:
        """Calls Groq API expecting a JSON object."""
        if not self.client:
            raise ValueError("Groq client not configured")
        completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=self.model,
            temperature=0.7,
            max_tokens=3000,
            response_format={"type": "json_object"}
        )
        content = completion.choices[0].message.content
        return self._extract_json(content)

    def _call_pollinations_json(self, system_prompt: str, user_prompt: str) -> dict:
        """Calls Pollinations AI text endpoint expecting a JSON object with robust timeout and multi-endpoint fallback."""
        headers = {}
        if self.pollinations_api_key:
            headers["Authorization"] = f"Bearer {self.pollinations_api_key}"

        # Attempt 1: Fast POST with jsonMode and realistic 28-second timeout
        url_post = "https://text.pollinations.ai/"
        payload = {
            "messages": [
                {"role": "system", "content": f"{system_prompt}\nCRITICAL: Output strictly a valid, raw JSON object only. No markdown fences, no explanatory text."},
                {"role": "user", "content": user_prompt}
            ],
            "model": "openai-fast",
            "jsonMode": True
        }
        try:
            res = requests.post(url_post, json=payload, headers=headers, timeout=28)
            if res.status_code == 200 and res.text.strip():
                data = self._extract_json(res.text)
                if data:
                    self.last_pollinations_time = time.time()
                    return data
            elif res.status_code in [402, 429]:
                print("[LLMService] Pollinations AI rate limit active.")
        except Exception as post_err:
            print(f"[LLMService] Pollinations POST attempt note: {post_err}")

        # Attempt 2: GET endpoint fallback with URL-encoded query
        try:
            combined_prompt = f"{system_prompt}\n\nTask: {user_prompt}\n\nReturn strictly valid JSON only."
            encoded = urllib.parse.quote(combined_prompt)
            url_get = f"https://text.pollinations.ai/{encoded}?model=openai-fast"
            res = requests.get(url_get, headers=headers, timeout=25)
            if res.status_code == 200 and res.text.strip():
                data = self._extract_json(res.text)
                if data:
                    self.last_pollinations_time = time.time()
                    return data
        except Exception as get_err:
            print(f"[LLMService] Pollinations GET attempt note: {get_err}")

        raise Exception("Pollinations request failed across all methods")

    # -------------------------------------------------------------
    # UNIFIED AI STRATEGY + SCRIPT GENERATION (ONE-SHOT COHERENCE)
    # -------------------------------------------------------------
    def generate_strategy_and_script(
        self,
        topic: str,
        audience: str = "General Audience",
        platform: str = "YouTube Shorts",
        duration: int = 60,
        goal: str = "Educate",
        tone: str = "Educational",
        language: str = "English"
    ) -> dict:
        """
        Generates BOTH director strategy AND the scene-by-scene script in a single unified AI call.
        Eliminates secondary rate-limit collisions and guarantees 100% coherence and exact topic adherence.
        """
        clean_topic = self._clean_topic_name(topic)
        # Extract number if topic mentions a specific count (e.g. "5 Morning Habits", "3 Tips", "7 Steps")
        count_match = re.search(r'\b(\d+)\s*(?:habits?|tips?|ways?|steps?|secrets?|rules?|keys?|points?|lessons?|mistakes?)\b', clean_topic, re.IGNORECASE)
        if count_match:
            detected_count = int(count_match.group(1))
            scenes_count = max(3, min(8, detected_count))
        else:
            scenes_count = max(3, min(8, int(duration // 12) or 5))
        scene_duration = round(duration / scenes_count, 1)

        system_prompt = (
            "You are an elite AI Video Director and YouTube scriptwriter. "
            "Output strictly a valid raw JSON object only with no markdown formatting."
        )

        user_prompt = f"""Create a high-retention video production strategy AND scene-by-scene script on the topic: "{topic}".

CRITICAL INSTRUCTIONS:
1. Every single scene MUST be 100% DIRECTLY, CONCRETELY, and SPECIFICALLY about "{clean_topic}".
2. Every scene MUST be completely unique. Do NOT repeat or duplicate previous scenes, headlines, or narrations.
3. Generate exactly {scenes_count} distinct scenes.
4. Do NOT mention unrelated Greek mythology, unrelated books, historical tangents, or generic filler.
5. Keep the narration natural, engaging, and spoken-word friendly.
6. Total duration: {duration} seconds across exactly {scenes_count} scenes (approx {scene_duration}s per scene).
7. HOOK & OPENING SCENE UNIQUENESS (STRICT):
   - NEVER start with formulaic clichés like "What if everything you were told about [topic] was only half the story?", "Stop overcomplicating [topic]", "Have you ever wondered", or "In this video we will explore".
   - Scene 1 narration MUST be a 100% unique, punchy opening sentence that dives straight into an intriguing observation or practical insight specifically about "{clean_topic}".

Return ONLY valid JSON matching this exact structure:
{{
  "strategy": {{
    "title": "High-converting title specifically about {clean_topic}",
    "hook": "Attention-grabbing opening hook specifically about {clean_topic}",
    "recommended_duration": {duration},
    "style": "Fast-paced cinematic {tone}",
    "scenes_count": {scenes_count},
    "voice_style": "Professional Male",
    "caption_style": "Bold Highlight",
    "cta": "Engaging call-to-action specifically about {clean_topic}"
  }},
  "script": {{
    "title": "Title specifically about {clean_topic}",
    "hook": "Opening hook specifically about {clean_topic}",
    "audience": "{audience}",
    "goal": "{goal}",
    "tone": "{tone}",
    "platform": "{platform}",
    "duration": {duration},
    "scenes": [
      {{
        "scene_id": 1,
        "duration": {scene_duration},
        "narration": "2 to 3 engaging sentences introducing {clean_topic} and its core benefit.",
        "on_screen_text": "2 to 4 words headline",
        "visual_description": "Cinematic photorealistic image prompt specifically showing {clean_topic}, 8k, photorealistic",
        "transition": "fade"
      }}
    ],
    "cta": "Engaging call-to-action specifically about {clean_topic}"
  }}
}}"""

        # Tier 1: Groq API
        if self.client:
            try:
                print(f"[LLMService] Generating strategy + script via Groq for '{clean_topic}'...")
                data = self._call_groq_json(system_prompt, user_prompt)
                strat = data.get("strategy", {})
                sc = data.get("script", {})
                if self._validate_strategy_data(strat) and self._validate_script_data(sc):
                    cleaned_sc = self._clean_script_data(sc, topic, strat, duration, scenes_count)
                    self._cached_scripts[clean_topic] = cleaned_sc
                    return {"strategy": strat, "script": cleaned_sc}
            except Exception as e:
                print(f"[LLMService] Groq error in generate_strategy_and_script: {e}")

        # Tier 2: Pollinations AI
        try:
            print(f"[LLMService] Generating strategy + script via Pollinations AI for '{clean_topic}'...")
            data = self._call_pollinations_json(system_prompt, user_prompt)
            strat = data.get("strategy", {})
            sc = data.get("script", {})
            if self._validate_strategy_data(strat) and self._validate_script_data(sc):
                cleaned_sc = self._clean_script_data(sc, topic, strat, duration, scenes_count)
                self._cached_scripts[clean_topic] = cleaned_sc
                return {"strategy": strat, "script": cleaned_sc}
        except Exception as e:
            print(f"[LLMService] Pollinations error in generate_strategy_and_script: {e}")

        # Tier 3: Direct topic synthesis engine (100% relevant, no Wikipedia)
        print(f"[LLMService] Synthesizing topic-specific strategy & script for '{clean_topic}'...")
        strat = self._generate_topic_specific_strategy(topic, audience, platform, duration, goal, tone)
        sc = self._synthesize_topic_specific_script(topic, strat, audience, goal, tone, platform, duration, scenes_count)
        self._cached_scripts[clean_topic] = sc
        return {"strategy": strat, "script": sc}

    # -------------------------------------------------------------
    # AI STRATEGY GENERATION
    # -------------------------------------------------------------
    def generate_strategy(self, topic: str, audience: str = "General Audience", platform: str = "YouTube Shorts", duration: int = 60, goal: str = "Educate", tone: str = "Educational", language: str = "English") -> dict:
        """Generates a comprehensive video strategy tailored specifically to the topic and pre-populates script cache."""
        res = self.generate_strategy_and_script(topic, audience, platform, duration, goal, tone, language)
        return res.get("strategy", {})

    # -------------------------------------------------------------
    # AI SCRIPT GENERATION (STRICT TOPIC ADHERENCE)
    # -------------------------------------------------------------
    def generate_script(
        self, 
        topic: str, 
        strategy: dict, 
        audience: str = "General Audience", 
        goal: str = "Educate", 
        tone: str = "Educational", 
        platform: str = "YouTube Shorts", 
        language: str = "English",
        force_regenerate: bool = False
    ) -> dict:
        """Generates an in-depth, scene-by-scene script strictly tailored to the user's topic."""
        clean_topic = self._clean_topic_name(topic)
        duration = strategy.get("recommended_duration", 60)
        scenes_count = strategy.get("scenes_count", max(3, min(8, int(duration // 10) or 5)))
        scene_duration = round(duration / scenes_count, 1)

        # Check if we have a fresh cached script for this exact topic & title (bypassed if force_regenerate is True)
        if force_regenerate:
            self._cached_scripts.pop(clean_topic, None)
        else:
            cached = self._cached_scripts.get(clean_topic)
            if cached and self._validate_script_data(cached):
                strat_title = strategy.get("title", "")
                cached_title = cached.get("title", "")
                if not strat_title or strat_title == cached_title or cached_title == clean_topic:
                    print(f"[LLMService] Using pre-generated topic script for '{clean_topic}'")
                    return cached

        system_prompt = "You are an expert video producer and scriptwriter. Output strictly valid raw JSON only."
        user_prompt = f"""Write an engaging, high-retention video script specifically on: "{clean_topic}".
Title: "{strategy.get('title', clean_topic)}"
Opening Hook: "{strategy.get('hook', 'Important facts about ' + clean_topic)}"
Target Audience: {audience}. Goal: {goal}. Tone: {tone}. Platform: {platform}. Target Duration: {duration}s. Scenes: {scenes_count}.

CRITICAL INSTRUCTIONS:
1. Every scene must directly, concretely explain and explore "{clean_topic}".
2. Do NOT mention unrelated Greek mythology, unrelated books, historical tangents, or generic filler.
3. For each scene:
   - "on_screen_text": A concise 2 to 4-word headline.
   - "narration": 2 to 3 informative, captivating sentences directly addressing {clean_topic}.
   - "visual_description": A cinematic, photorealistic visual scene description specifically featuring {clean_topic}, 8k.
4. NEVER start Scene 1 with generic clichés like "What if everything you were told about [topic] was only half the story?". Dive straight into a fresh, captivating opening sentence unique to {clean_topic}.

Return ONLY valid JSON matching this schema:
{{
  "title": "{strategy.get('title', clean_topic)}",
  "hook": "{strategy.get('hook', 'Opening hook about ' + clean_topic)}",
  "audience": "{audience}",
  "goal": "{goal}",
  "tone": "{tone}",
  "platform": "{platform}",
  "duration": {duration},
  "scenes": [
    {{
      "scene_id": 1,
      "duration": {scene_duration},
      "narration": "2 to 3 informative sentences directly on {clean_topic}",
      "on_screen_text": "2 to 4 word headline",
      "visual_description": "Cinematic visual description depicting {clean_topic}, photorealistic, 8k",
      "transition": "fade"
    }}
  ],
  "cta": "{strategy.get('cta', 'Follow for more insights on ' + clean_topic + '!')}"
}}"""

        # Tier 1: Groq API
        if self.client:
            try:
                print(f"[LLMService] Generating detailed script via Groq for '{clean_topic}'...")
                data = self._call_groq_json(system_prompt, user_prompt)
                if self._validate_script_data(data):
                    cleaned = self._clean_script_data(data, topic, strategy, duration, scenes_count)
                    self._cached_scripts[clean_topic] = cleaned
                    return cleaned
            except Exception as e:
                print(f"[LLMService] Groq API error in generate_script: {e}")

        # Tier 2: Free Pollinations AI
        try:
            print(f"[LLMService] Generating detailed script via Pollinations AI for '{clean_topic}'...")
            data = self._call_pollinations_json(system_prompt, user_prompt)
            if self._validate_script_data(data):
                cleaned = self._clean_script_data(data, topic, strategy, duration, scenes_count)
                self._cached_scripts[clean_topic] = cleaned
                return cleaned
        except Exception as e:
            print(f"[LLMService] Pollinations AI error in generate_script: {e}")

        # Tier 3: Topic-Specific Synthesis Fallback
        print(f"[LLMService] Synthesizing topic-specific script for '{clean_topic}'...")
        sc = self._synthesize_topic_specific_script(topic, strategy, audience, goal, tone, platform, duration, scenes_count)
        self._cached_scripts[clean_topic] = sc
        return sc

    # -------------------------------------------------------------
    # AI SOCIAL POST GENERATION
    # -------------------------------------------------------------
    def generate_social_post(self, topic: str, title: str = "", hook: str = "", platform: str = "YouTube Shorts", audience: str = "General Audience", goal: str = "Educate", tone: str = "Educational", language: str = "English") -> dict:
        """Generates viral, engaging social media captions and hyper-relevant hashtags."""
        clean = self._clean_topic_name(topic)
        system_prompt = "You are a world-class viral social media manager. Output strictly valid raw JSON only."
        user_prompt = f"""Write a viral social post for video: "{topic}". Title: "{title or topic}". Platform: {platform}.
Output JSON with:
"caption": "Full high-converting post with emojis, 3 bullet takeaways on {topic}, and CTA",
"short_caption": "1-sentence punchy mobile caption",
"call_to_action": "Follow and save CTA",
"hashtags": ["#Tag1", "#Tag2", "#Tag3", "#Tag4", "#Tag5"],
"hashtags_string": "#Tag1 #Tag2 #Tag3 #Tag4 #Tag5",
"platform_variations": {{"youtube_shorts": "Text", "instagram_reels": "Text", "tiktok": "Text", "linkedin": "Text"}},
"engagement_question": "Engaging question about {topic} to pin in comments"
"""

        # Tier 1: Groq API
        if self.client:
            try:
                print(f"[LLMService] Generating social post via Groq for '{topic}'...")
                data = self._call_groq_json(system_prompt, user_prompt)
                if self._validate_social_post_data(data):
                    return self._format_social_post_data(data, clean)
            except Exception as e:
                print(f"[LLMService] Groq API error in generate_social_post: {e}")

        # Tier 2: Free Pollinations AI
        try:
            print(f"[LLMService] Generating social post via Pollinations AI for '{topic}'...")
            data = self._call_pollinations_json(system_prompt, user_prompt)
            if self._validate_social_post_data(data):
                return self._format_social_post_data(data, clean)
        except Exception as e:
            print(f"[LLMService] Pollinations AI error in generate_social_post: {e}")

        # Tier 3: Contextual fallback
        return self._generate_topic_specific_social_post(topic, title, hook, platform, audience, goal, tone)

    # -------------------------------------------------------------
    # TOPIC-SPECIFIC SCRIPT SYNTHESIS (100% RELEVANT & NO WIKIPEDIA POLLUTION)
    # -------------------------------------------------------------
    def _synthesize_topic_specific_script(self, topic: str, strategy: dict, audience: str, goal: str, tone: str, platform: str, duration: int, scenes_count: int) -> dict:
        """Synthesizes high-depth, topic-specific script tailored 100% to the user's topic."""
        clean = self._clean_topic_name(topic)
        scene_duration = round(duration / scenes_count, 1)

        title = strategy.get("title") or f"{clean}: The Complete Guide"
        hook = strategy.get("hook") or f"Have you ever wondered what really makes {clean} so powerful?"
        cta = strategy.get("cta") or f"Follow for more insights on {clean} and share this with a friend!"

        # Domain classification by priority using word boundaries to prevent false substring matches
        lower_topic = clean.lower()
        def _match(pattern: str) -> bool:
            return bool(re.search(r'\b(' + pattern + r')\b', lower_topic))

        if _match(r'cyber|cybersecurity|security|hack|hacking|hacker|remote\s+work\w*|phish\w*|vpn|malware|auth|mfa'):
            domain = "cybersecurity"
        elif _match(r'pizza\w*'):
            domain = "pizza"
        elif _match(r'burger\w*|patty|patties|smash\s*burger|bbq|grill\w*|steak\w*'):
            domain = "food_burger"
        elif _match(r'espresso|coffee|brew\w*|barista|cappuccino|latte\w*'):
            domain = "food_coffee"
        elif _match(r'sourdough|bread|baking|bake\w*|dough|flour|pastry|croissant'):
            domain = "food_bread"
        elif _match(r'pasta\w*|spaghetti|noodles?|lasagna|ravioli|italian\s+food'):
            domain = "food_pasta"
        elif _match(r'sushi|ramen|sashimi|japanese\s+food'):
            domain = "food_sushi"
        elif _match(r'car|tire|tires|mechanic|engine|automotive|vehicle|brake\w*|oil\s+change'):
            domain = "automotive"
        elif _match(r'guitar\w*|fretboard|chords?|strum\w*|acoustic|electric\s+guitar'):
            domain = "music_guitar"
        elif _match(r'piano|pianist|keyboard|drums?|violin|instruments?|music\w*'):
            domain = "music"
        elif _match(r'dogs?|puppy|puppies|retriever|canine|dog\s+training|pets?'):
            domain = "pets"
        elif _match(r'space|astronomy|mars|moon|nasa|telescope|galaxy|planets?|cosmos|star\w*'):
            domain = "space"
        elif _match(r'garden\w*|plants?|soil|indoor\s+plants|succulents?|farming'):
            domain = "gardening"
        elif _match(r'back\s+pain|posture|spine|lumbar|neck\s+pain'):
            domain = "back_pain"
        elif _match(r'workout\w*|gym|fitness|muscle\w*|bodybuilding|strength|lifting|running|cardio'):
            domain = "fitness"
        elif _match(r'coding|python|programming|javascript|software|developer|web\s+dev\w*|algorithm\w*'):
            domain = "coding"
        elif _match(r'recipe\w*|cook\w*|dish\w*|meal\w*|kitchen|culinary|cuisine|snack|taco\w*|sandwich\w*|soup'):
            domain = "culinary"
        elif _match(r'productivity|productive|habit\w*|routine\w*|focus|procrastinat\w*|discipline|time\s+management|morning\s+routine|mindset|goals?'):
            domain = "productivity"
        elif _match(r'yoga|meditat\w*|mindfulness|stress|wellness|sleep|insomnia|relaxation|fasting'):
            domain = "wellness"
        elif _match(r'quantum|qubits?|ai|machine\s+learning|computers?|robots?|cloud'):
            domain = "technology"
        elif _match(r'home\w*|house|room\w*|decor|zen|peaceful|interior|declutter\w*|sanctuary|living\s+room|bedroom|kitchen|apartment|cozy'):
            domain = "home_living"
        elif _match(r'money|invest\w*|finance|financial|business|markets?|wealth|stocks?|career|startups?|passive\s+income|crypto|real\s+estate'):
            domain = "finance"
        elif _match(r'animals?|wildlife|lions?|tigers?|wolves|wolf|bears?|beasts?|creatures?|predators?|safari|species'):
            domain = "wildlife"
        elif _match(r'trees?|nature|earth|climate|biology|physics|solar|oceans?|forests?'):
            domain = "science"
        elif _match(r'rome|ancient|centur\w+|empires?|kings?|revolutions?|dynast\w+|civilization|medieval|samurai|history'):
            domain = "history"
        else:
            domain = "general"

        domain_blueprints = {
            "automotive": [
                ("Safety & Setup", f"Before touching a tool on {clean}, park on flat solid ground, engage the emergency brake, and secure wheel chocks.", "intro"),
                ("Loosen Lug Nuts", "Break the initial resistance on each wheel lug nut with your wrench while the tire still rests firmly on the ground.", "mechanism"),
                ("Jack Up Vehicle", "Position the hydraulic jack securely under the reinforced metal pinch weld and raise the car three inches off the ground.", "detail"),
                ("Swap the Wheel", "Unscrew the lug nuts, pull off the flat tire, mount the replacement onto the wheel studs, and hand-tighten nuts in a star pattern.", "application"),
                ("Torque to Spec", f"Lower the vehicle to the pavement, remove the jack, and firmly torque all lug nuts in an alternating criss-cross star pattern. {cta}", "outro")
            ],
            "music_guitar": [
                ("Fretboard Grip", f"Great tone in {clean} starts with thumb positioning: place your thumb behind the neck center to maximize finger stretch.", "intro"),
                ("Clean Fret Placement", "Press your fingertips close to the metal fret wire rather than in the middle to eliminate fret buzz with minimal pressure.", "mechanism"),
                ("Rhythm & Strumming", "Keep your strumming wrist relaxed like a pendulum, maintaining a consistent down-up rhythm regardless of chord changes.", "detail"),
                ("Smooth Chord Shifts", "Anchor your index finger and anticipate the next chord shape one beat before moving to make shifts seamless.", "application"),
                ("Musical Freedom", f"Consistent daily ten-minute practice locks in muscle memory and unlocks effortless playing. Keep strumming! {cta}", "outro")
            ],
            "food_burger": [
                ("80/20 Ground Beef", f"The secret to an unforgettable {clean} begins with cold ground chuck with an 80/20 lean-to-fat ratio seasoned right before cooking.", "intro"),
                ("High-Heat Smash", "Preheat a cast-iron skillet until smoking hot and smash the meat patty paper-thin to lock in that crispy caramelized Maillard crust.", "mechanism"),
                ("The Melty Cheese Dome", "Place sharp cheddar over the searing patty and cover with a metal lid for thirty seconds to create a decadent molten cheese blanket.", "detail"),
                ("Toasted Brioche Bun", "Butter and toast your brioche bun until golden crisp so it holds savory juices without turning soggy.", "application"),
                ("Signature Assembly", f"Layer crisp lettuce, pickles, and burger sauce for that perfect first bite. Fire up your skillet and enjoy! {cta}", "outro")
            ],
            "food_coffee": [
                ("Dialing the Grind", f"World-class {clean} comes down to grind distribution: grinding fresh whole beans to the exact micron level for balanced resistance.", "intro"),
                ("WDT & Level Tamp", "De-clump grounds with needle distribution and tamp completely flat to prevent uneven water channeling through the puck.", "mechanism"),
                ("9-Bar Extraction", "Brew under nine bars of pressure for twenty-five seconds to yield thick, honey-like extraction crowned with golden crema.", "detail"),
                ("Velvety Microfoam", "Texture cold milk into glossy microfoam with microscopic air bubbles that naturally sweetens your pour.", "application"),
                ("Artisan Presentation", f"Pour through the crema with controlled flow to finish with delicate latte art. Savor every single sip! {cta}", "outro")
            ],
            "food_bread": [
                ("Active Starter Feeding", f"The foundation of exceptional {clean} begins with a mature, bubbly wild yeast starter fed at peak fermentation activity.", "intro"),
                ("Autolyse & Stretch", "Mix flour and water to develop gluten gently, using rhythmic stretch-and-folds rather than aggressive heavy kneading.", "mechanism"),
                ("Bulk Cold Ferment", "Allow the shaped dough to ferment cold in the refrigerator overnight, producing complex lactic acid flavors and blistered crust.", "detail"),
                ("Scoring & Steam Bake", "Score the top with a razor blade and bake inside a preheated Dutch oven to trap steam for maximum oven spring and ear lift.", "application"),
                ("The Crackling Crumb", f"Let the loaf cool completely before slicing to reveal an airy, open crumb and crackling artisan crust. Happy baking! {cta}", "outro")
            ],
            "food_pasta": [
                ("Egg & Semolina Dough", f"Authentic fresh {clean} starts with high-grade Italian '00' flour and rich egg yolks kneaded into a smooth, elastic golden dough.", "intro"),
                ("Sheeting Paper-Thin", "Roll the rested dough through pasta rollers gradually until it reaches delicate translucent thickness.", "mechanism"),
                ("Salted Rolling Boil", "Drop fresh noodles into generously salted boiling water for just two to three minutes until perfectly al dente.", "detail"),
                ("Emulsified Sauce Finish", "Vigorously toss the pasta with cooking water and butter or pecorino to create a glossy, clingy emulsion.", "application"),
                ("The Italian Table", f"Fresh handmade pasta turns simple cooking into pure artisan joy. Plate with fresh parmesan and enjoy! {cta}", "outro")
            ],
            "pets": [
                ("Marker Timing", f"Effective training with {clean} starts with clear marker timing—marking the exact second of good behavior with a click or praise.", "intro"),
                ("High-Value Rewards", "Use irresistible treats like real chicken or cheese to keep motivation, engagement, and focus at peak levels.", "mechanism"),
                ("Short Training Bursts", "Dogs learn dramatically faster in brief three-to-five minute sessions spread through the day rather than exhausting long blocks.", "detail"),
                ("Gradual Distractions", "Only introduce distance, duration, and outdoor distractions once the behavior is completely reliable inside a quiet room.", "application"),
                ("Lifelong Companionship", f"Consistency, patience, and positive reinforcement build a deep bond of trust and obedience. Give your pet a hug! {cta}", "outro")
            ],
            "space": [
                ("The Cosmic Frontier", f"Exploring {clean} takes us beyond human horizons to observe the violent, breathtaking physics shaping our universe.", "intro"),
                ("Orbital Trajectories", "Reaching deep space demands extreme precision: calculating escape velocity, gravitational slingshots, and propulsion burns.", "mechanism"),
                ("Deep Space Observatories", "Next-generation infrared instruments peer through cosmic dust to capture ancient light from the first stars and galaxies.", "detail"),
                ("The Search for Life", "Astronomers scan exoplanet atmospheres for biosignatures like water vapor, methane, and oxygen that hint at habitable worlds.", "application"),
                ("Our Place in the Stars", f"Studying {clean} reminds us that we are stardust exploring the magnificent cosmos. Keep looking up! {cta}", "outro")
            ],
            "gardening": [
                ("Living Soil Prep", f"Vibrant growth with {clean} starts beneath the surface: aerating the soil and blending nutrient-rich organic compost.", "intro"),
                ("Matching Photoperiod", "Position plants according to their specific light needs—full direct sun versus gentle filtered morning light.", "mechanism"),
                ("Deep Morning Watering", "Water deeply at the root base in early morning so moisture reaches root systems before afternoon heat evaporates it.", "detail"),
                ("Pruning for Abundance", "Pinch off suckers and dead growth to redirect plant energy into strong stems and abundant harvest.", "application"),
                ("Bountiful Harvest", f"Gardening is the rewarding art of daily patience. Enjoy your thriving green sanctuary! {cta}", "outro")
            ],
            "back_pain": [
                ("The Posture Breakdown", f"Chronic discomfort from {clean} usually stems from sitting too long, locked hip flexors, and dormant stabilizing muscles.", "intro"),
                ("Spinal Decompression", "Decompress your lumbar discs gently with active hanging or cat-cow stretches to restore intervertebral spacing.", "mechanism"),
                ("Glute & Core Activation", "Strengthen your glute bridges and transverse abdominis to support your pelvis and take pressure off your lower spine.", "detail"),
                ("Micro-Movement Breaks", "Stand up and perform gentle hip openers and thoracic twists every forty-five minutes to reset postural alignment.", "application"),
                ("Lasting Mobility", f"Consistent daily movement restores healthy biomechanics and pain-free freedom. Keep moving every day! {cta}", "outro")
            ],
            "coding": [
                ("Logical Architecture", f"Writing clean software in {clean} starts with decomposition: breaking complex requirements into small, modular functions.", "intro"),
                ("Data Structure Choice", "Choosing the right data structure—dictionaries, sets, or lists—is what separates efficient code from sluggish bottlenecks.", "mechanism"),
                ("Automated Testing", "Write unit tests for critical edge cases so you can refactor confidently without breaking production functionality.", "detail"),
                ("Refactoring & Clean Code", "Eliminate code smells by keeping functions pure, names descriptive, and avoiding premature optimization.", "application"),
                ("Shipping Value", f"Writing code is a superpower that transforms ideas into scalable software. Build, test, and ship your creation! {cta}", "outro")
            ],
            "home_living": [
                ("Declutter Surfaces", f"Creating a peaceful home begins with intentional space. Clearing surfaces and removing visual clutter immediately signals tranquility to your brain.", "intro"),
                ("Warm Lighting", "Lighting sets the emotional temperature of your home. Replacing harsh overhead lights with warm lamps and soft natural sunlight instantly melts tension away.", "mechanism"),
                ("Sensory Harmony", "Incorporate biophilic elements like indoor greenery, breathable linen textures, and calming natural scents such as lavender or eucalyptus.", "detail"),
                ("Tech-Free Nook", "Designate a dedicated quiet corner free from screens and notifications where you can read, meditate, and recharge your energy in peace.", "application"),
                ("Daily Sanctuary", f"A truly peaceful home isn't about perfection—it's about protecting your peace of mind and building daily calm. {cta}", "outro")
            ],
            "cybersecurity": [
                ("Perimeter Defense", f"Securing your digital environment starts with awareness. Most breaches exploit weak credentials and deceptive phishing attacks rather than complex hacks.", "intro"),
                ("Multi-Factor Shield", "Enforce multi-factor authentication across every sensitive tool. A secondary verification step stops over 99% of automated credential stuffing attacks.", "mechanism"),
                ("Encrypted Network", "Never transmit confidential data across unencrypted networks. Always route work through dedicated encrypted tunnels and verified VPN connections.", "detail"),
                ("Automated Updates", "Keep operating systems and security patches up to date. Software vulnerabilities are patched constantly, and delayed updates leave doors wide open.", "application"),
                ("Digital Resilience", f"Robust security is a disciplined daily habit, not a one-time setup. Protect your data and share this protocol with your peers! {cta}", "outro")
            ],
            "pizza": [
                ("Dough Fermentation", f"The secret to extraordinary {clean} begins with slow cold fermentation, creating airy crust bubbles and rich savory depth.", "intro"),
                ("Sauce & Simplicity", f"Simplicity defines great {clean}: crushed San Marzano tomatoes, fresh mozzarella, and fragrant whole-leaf basil create the timeless flavor harmony.", "mechanism"),
                ("Blistering Heat", f"Baking {clean} at intense maximum heat gives that signature leopard-spotted crust and perfectly melted, bubbling cheese stretch.", "detail"),
                ("Finishing Drizzle", "A light swirl of cold-pressed extra virgin olive oil and freshly cracked sea salt right out of the oven elevate every slice to artisan quality.", "application"),
                ("The Perfect Slice", f"Great {clean} is an art anyone can master with patience, high heat, and passion. Fire up your oven and share this slice! {cta}", "outro")
            ],
            "culinary": [
                ("Pristine Ingredients", f"The secret to exceptional {clean} begins with selecting pristine, high-grade ingredients and understanding the precise ratio of every component.", "intro"),
                ("Heat & Technique", "Precise temperature control and balanced timing extract rich depth and vibrant aromas without scorching delicate flavor notes.", "mechanism"),
                ("Layering Flavors", "Balance acidity, richness, and seasoning at every step to elevate ordinary cooking into an unforgettable culinary experience.", "detail"),
                ("Artisan Presentation", "Presenting with mindful visual contrast and garnish turns every meal into an inviting celebration of craftsmanship.", "application"),
                ("The Dining Table", f"Great culinary craft brings warmth to any gathering. Master the fundamentals and share your creation with joy. {cta}", "outro")
            ],
            "technology": [
                ("Core Innovation", f"Examining {clean} reveals a transformative technological architecture designed to solve complex modern challenges.", "intro"),
                ("Processing Pipeline", "At its core, intelligent data workflows and low-latency processing ensure seamless execution and optimal performance.", "mechanism"),
                ("Security & Scale", "Robust cryptographic validation and automated error resilience protect system integrity as user demand scales.", "detail"),
                ("Real-World Impact", "Practical implementation bridges theoretical capability with tangible efficiency gains across modern engineering stacks.", "application"),
                ("The Next Frontier", f"As innovation accelerates, mastering {clean} unlocks unprecedented potential for creators and developers alike. {cta}", "outro")
            ],
            "productivity": [
                ("Ruthless Focus", f"Mastering {clean} starts with clear prioritization. Choosing just one non-negotiable objective each morning eliminates decision fatigue.", "intro"),
                ("Deep Work Sprints", "Protect distraction-free 90-minute blocks where all notifications are silenced. High-focus sprints consistently outperform scattered multitasking.", "mechanism"),
                ("Habit Stacking", "Anchor new productive routines onto habits you already perform daily, making consistency nearly effortless over time.", "detail"),
                ("Active Recovery", "High performers treat active rest with the same intentionality as deep work. Stepping away resets your mental clarity and sparks fresh creativity.", "application"),
                ("Compounding Gains", f"Small, disciplined daily habits compound exponentially over time. Master your daily systems, and results follow naturally. {cta}", "outro")
            ],
            "wellness": [
                ("Morning Vitality", f"True wellness with {clean} starts with biological harmony. Hydration, morning sunlight, and mindful movement build an unshakeable foundation of daily energy.", "intro"),
                ("Consistent Rhythm", "Support your nervous system by establishing a consistent sleep schedule and dialing down screen exposure before bed.", "mechanism"),
                ("Mind-Body Reset", "Controlled diaphragmatic breathing activates the parasympathetic response, reducing cortisol and centering your thoughts.", "detail"),
                ("Nourish & Recover", "Fuel your body with wholesome nutrients and prioritize physical recovery so your muscles and mind can rebuild stronger.", "application"),
                ("Sustainable Life", f"Health is a lifelong journey of sustainable habits rather than extreme rules. Celebrate every small step of progress. {cta}", "outro")
            ],
            "finance": [
                ("Strategic Foundation", f"Building lasting success in {clean} requires an unshakeable understanding of cash flow, asset allocation, and value creation.", "intro"),
                ("Compounding Growth", "The most powerful wealth mechanism is compound interest. Reinvesting returns consistently outperforms trying to time the market.", "mechanism"),
                ("Risk Mitigation", "Protect your downside with diversification and calculated risk management before pursuing high-velocity growth.", "detail"),
                ("Scalable Systems", "Focus on building repeatable, automated financial systems that generate returns independently of your direct hours.", "application"),
                ("Financial Freedom", f"True financial independence is about creating freedom over your time. Stick to disciplined fundamentals for the long term. {cta}", "outro")
            ],
            "science": [
                ("Natural Phenomenon", f"Exploring {clean} reveals the profound physical and biological mechanisms that govern the natural world.", "intro"),
                ("Dynamic Interaction", "Intricate molecular and environmental interactions work in harmony to produce extraordinary natural efficiency.", "mechanism"),
                ("Ecological Balance", "Each component serves a vital role in sustaining balance across interconnected ecosystems and biological cycles.", "detail"),
                ("Breakthrough Insight", "Modern scientific research continues to unveil deeper layers of understanding and practical applications.", "application"),
                ("Universal Harmony", f"Understanding the true nature of {clean} expands our awe for the universe and inspires future discovery. {cta}", "outro")
            ],
            "general": [
                ("Preparation & Tools" if "how" in lower_topic or "guide" in lower_topic or "tips" in lower_topic else "The Core Breakdown", f"Getting started with {clean} requires understanding the foundational principles and setting up your approach with clear intent.", "intro"),
                ("Essential Technique" if "how" in lower_topic or "guide" in lower_topic or "tips" in lower_topic else "Key Mechanics", f"The heart of mastering {clean} is understanding the primary mechanics and executing with deliberate focus.", "mechanism"),
                ("Precision & Control" if "how" in lower_topic or "guide" in lower_topic or "tips" in lower_topic else "Real-World Evidence", f"Avoid rushing through {clean}: maintain steady control, verify your alignment, and focus on smooth repetition.", "detail"),
                ("Common Pitfalls" if "how" in lower_topic or "guide" in lower_topic or "tips" in lower_topic else "Practical Impact", f"The most frequent mistake in {clean} is skipping small foundational details that compound into errors later.", "application"),
                ("Mastery & Polish" if "how" in lower_topic or "guide" in lower_topic or "tips" in lower_topic else "The Big Picture", f"Consistent, mindful execution of these principles on {clean} delivers exceptional results every single time. {cta}", "outro")
            ]
        }

        # Check if topic specifically asks for habits / morning routine
        is_habit_topic = bool(re.search(r'\b(habit\w*|morning\w*|routine\w*)\b', lower_topic))
        if is_habit_topic and domain in ["productivity", "wellness", "general"]:
            blueprint = [
                ("Habit 1: Morning Sunlight", f"Step into natural morning sunlight within thirty minutes of waking. This anchors your circadian rhythm, clears brain fog, and triggers natural alert focus.", "intro"),
                ("Habit 2: Ruthless Priority", "Habit two: Define your single most important high-leverage objective before touching emails or notifications. Guarding early morning clarity eliminates decision fatigue.", "mechanism"),
                ("Habit 3: Deep Work Sprint", "Habit three: Protect a distraction-free ninety-minute block where your phone is completely silent. High-focus sprints consistently produce extraordinary output.", "detail"),
                ("Habit 4: Mindful Movement", "Habit four: Incorporate brisk movement, hydration, or mobility stretching to stimulate blood flow, oxygenate your brain, and raise dopamine naturally.", "application"),
                ("Habit 5: Daily Reflection", f"Habit five: Review your progress at dusk and set tomorrow's clear priorities. Small, disciplined morning habits compound exponentially over time. {cta}", "outro")
            ]
        else:
            blueprint = domain_blueprints.get(domain, domain_blueprints["general"])

        # NEVER duplicate scenes: clamp scenes_count to blueprint length
        actual_scenes_count = min(scenes_count, len(blueprint))
        scene_duration = round(duration / actual_scenes_count, 1)

        scenes = []
        for i in range(1, actual_scenes_count + 1):
            header_text, body_narration, phase = blueprint[i - 1]
            
            if i == 1:
                # Use topic-specific hook as the opening sentence if available, followed by body narration
                if hook and not any(h_word in body_narration[:40].lower() for h_word in ["step into", "the secret", "securing", "creating", "exploring", "when it comes"]):
                    narration = f"{hook} {body_narration}"
                else:
                    narration = body_narration
                text = header_text
                visual = self._get_domain_visual(domain, clean, "intro", header_text=header_text, narration=narration)
            elif i == actual_scenes_count:
                narration = body_narration
                text = "Key Takeaway" if "Takeaway" in header_text else header_text
                visual = self._get_domain_visual(domain, clean, "outro", header_text=text, narration=narration)
            else:
                narration = body_narration
                text = header_text
                visual = self._get_domain_visual(domain, clean, phase, header_text=header_text, narration=narration)

            scenes.append({
                "scene_id": i,
                "duration": scene_duration,
                "narration": narration.strip(),
                "visual_description": visual,
                "on_screen_text": text,
                "transition": "fade"
            })

        return {
            "title": title,
            "hook": hook,
            "audience": audience,
            "goal": goal,
            "tone": tone,
            "platform": platform,
            "duration": duration,
            "scenes": scenes,
            "cta": cta
        }

    def _get_domain_visual(self, domain: str, topic: str, phase: str, header_text: str = "", narration: str = "") -> str:
        """Constructs detailed, cinematic image generation prompts matching domain and context."""
        clean = topic.strip()
        combined_context = f"{header_text} {narration}".lower()
        if domain == "home_living":
            if phase == "intro":
                return f"Cinematic establishing shot of a sunlit, peaceful minimalist home sanctuary, soft ambient lighting, cozy neutral linen textures, indoor green plants, 8k resolution, photorealistic"
            elif phase == "mechanism":
                return f"Detailed close-up shot of mindful home decluttering and organized warm living space, soft morning rays through sheer curtains, tranquil aesthetic"
            elif phase == "detail":
                return f"Macro shot of aromatic diffuser with subtle vapor, warm table lamp, smooth ceramic decor, calming domestic atmosphere"
            elif phase == "application":
                return f"Serene reading nook with comfortable armchair, soft throw blanket, warm wooden floor, tranquil sanctuary ambience"
            else:
                return f"Inspiring wide-angle view of a beautifully balanced, calm living room bathed in golden sunset glow, feeling of absolute peace and serenity"
        elif domain == "cybersecurity":
            if phase == "intro":
                return f"Cinematic shot of modern cybersecurity operations center with glowing digital security shields, blue and green cyber matrix, photorealistic 8k"
            elif phase == "mechanism":
                return f"Close-up macro of smartphone displaying two-factor authentication prompt and secure biometric fingerprint scan, soft studio lighting"
            elif phase == "detail":
                return f"Encrypted data streams flowing through modern laptop workstation, holographic padlock security graphics, clean corporate desk"
            else:
                return f"Confident professional working securely on laptop in bright modern office, cyber defense shield icon subtle in background"
        elif domain == "productivity":
            if any(k in combined_context for k in ["sunlight", "sun", "waking", "morning light"]):
                return f"Person standing by window in natural morning sunlight drinking fresh water, healthy morning routine, warm sunrise illumination, 8k resolution, photorealistic"
            elif any(k in combined_context for k in ["priority", "planner", "planning", "journal", "time-blocking", "objective"]):
                return f"Detailed shot of structured time-blocking planner notebook, pen in hand, elegant desk setup, morning task prioritization, photorealistic 8k"
            elif any(k in combined_context for k in ["deep work", "focus", "sprint", "distraction-free", "laptop"]):
                return f"Clean minimalist laptop workstation on wooden desk displaying focus dashboard, quiet ambient lighting, focused productivity flow, 8k"
            elif any(k in combined_context for k in ["movement", "walk", "exercise", "hydration", "stretch", "mobility"]):
                return f"Motivated professional taking a refreshing mindful walk outdoors in morning fresh air, green park trees, clear headspace, crisp cinematography"
            elif any(k in combined_context for k in ["reflection", "review", "dusk", "tomorrow", "evening", "compound"]):
                return f"Aspirational modern home office overlooking city skyline at sunset dusk, organized completed tasks, calm reflection, feeling of accomplishment, 8k"
            elif phase == "intro":
                return f"Cinematic clean minimalist desk setup with modern notebook, warm morning coffee, soft natural window light, focused work environment, 8k"
            else:
                return f"Cinematic high-productivity workspace capturing {header_text or clean}, focused ambient lighting, 8k resolution, photorealistic"
        elif domain == "pizza":
            if any(k in combined_context for k in ["dough", "ferment", "flour", "knead", "bubble"]):
                return f"Cinematic close-up of artisan pizza dough dusted with flour, smooth round fermentation bubbles, warm Italian bakery lighting, photorealistic 8k"
            elif any(k in combined_context for k in ["sauce", "simplicity", "tomato", "basil", "mozzarella", "crushed"]):
                return f"Top-down view of freshly shaped pizza crust with rich red San Marzano tomato sauce, fresh mozzarella curd pieces, and green basil leaves, rustic culinary studio lighting"
            elif any(k in combined_context for k in ["heat", "oven", "blister", "fire", "bake", "wood", "leopard"]):
                return f"Cinematic action shot inside glowing wood-fired brick pizza oven, Neapolitan crust blistering with crisp leopard spots and bubbling melted cheese, 8k"
            elif any(k in combined_context for k in ["drizzle", "oil", "salt", "finish", "olive", "herb"]):
                return f"Close-up macro of fragrant extra virgin olive oil drizzling from stainless spout onto piping hot pizza with fresh basil and melted cheese, artisan kitchen"
            elif any(k in combined_context for k in ["slice", "perfect", "eat", "crust", "pull", "serve"]):
                return f"Steaming hot artisan pizza slice being pulled from whole pizza with long stretchy melted mozzarella cheese pull, blistered crust, mouthwatering gourmet food photography"
            elif phase == "intro":
                return f"Cinematic close-up establishing shot of artisan Neapolitan pizza dough and fresh ingredients on marble counter, soft warm Italian kitchen lighting, 8k photorealistic"
            else:
                return f"Mouthwatering gourmet artisan pizza with bubbling mozzarella, rich tomato sauce, and fresh basil on rustic wooden board, photorealistic 8k"
        elif domain == "automotive":
            if any(k in combined_context for k in ["lug", "wrench", "loosen", "nut", "wheel"]):
                return "Close-up of mechanic hands in work gloves using chrome lug wrench to loosen wheel lug nuts on modern car, crisp natural garage lighting, 8k"
            elif any(k in combined_context for k in ["jack", "lift", "raise", "hydraulic"]):
                return "Hydraulic car jack positioned under reinforced metal pinch weld lifting vehicle safely off asphalt ground, sharp focus, 8k"
            elif any(k in combined_context for k in ["swap", "tire", "spare", "mount"]):
                return "Mounting fresh replacement spare wheel onto car wheel hub studs, automotive service garage cinematography, 8k"
            elif any(k in combined_context for k in ["torque", "tighten", "spec", "lower"]):
                return "Using torque wrench on wheel lug nuts in alternating star pattern after lowering vehicle to road, professional automotive photography"
            else:
                return f"Clean cinematic establishing shot of car tire maintenance on {clean}, modern automotive garage setting, 8k"
        elif domain == "music_guitar":
            if any(k in combined_context for k in ["fret", "finger", "thumb", "neck"]):
                return "Close-up macro of musician fingers pressing clean chords on acoustic guitar wooden fretboard, warm studio lighting, 8k"
            elif any(k in combined_context for k in ["strum", "pick", "rhythm", "wrist"]):
                return "Right hand strumming acoustic guitar soundhole with plectrum, sound vibrations and golden acoustic wood finish, 8k"
            elif any(k in combined_context for k in ["shift", "transition", "chord"]):
                return "Dynamic angle of hands executing smooth chord transitions on guitar neck, warm ambient stage lighting, shallow depth of field"
            else:
                return "Pristine acoustic guitar resting on wooden stand beside music sheets, golden hour ambient window light, photorealistic 8k"
        elif domain == "food_burger":
            if any(k in combined_context for k in ["smash", "sear", "patty", "skillet", "beef"]):
                return "Sizzling beef burger patty searing on smoking hot cast-iron skillet, crispy caramelized Maillard crust edges, 8k gourmet food photography"
            elif any(k in combined_context for k in ["cheese", "melt", "cheddar", "dome"]):
                return "Thick sharp cheddar cheese melting decadently over sizzling burger patty under steam dome, dripping cheese, mouthwatering 8k"
            elif any(k in combined_context for k in ["bun", "brioche", "toast", "butter"]):
                return "Golden toasted buttered brioche burger buns on griddle with crisp edges, warm bakery lighting"
            else:
                return "Epic towering gourmet smash burger with melted cheddar, crisp lettuce, fresh pickles, and sauce on wooden board, 8k"
        elif domain == "food_coffee":
            if any(k in combined_context for k in ["grind", "wdt", "tamp", "puck"]):
                return "Barista leveling coffee grounds with WDT needle tool inside precision portafilter basket, artisan espresso bar lighting, 8k"
            elif any(k in combined_context for k in ["extract", "crema", "pressure", "pull"]):
                return "Bottomless portafilter extracting rich golden-brown espresso crema stream into clear glass cup, warm cafe atmosphere, 8k"
            elif any(k in combined_context for k in ["steam", "milk", "microfoam", "latte", "pour"]):
                return "Barista pouring velvety microfoam milk creating intricate tulip latte art into ceramic cup, glossy texture, 8k"
            else:
                return "Steaming hot artisan espresso crowned with thick golden crema on rustic wooden cafe table, soft morning backlight, 8k"
        elif domain == "food_bread":
            if any(k in combined_context for k in ["starter", "autolyse", "stretch", "dough"]):
                return "Baker hands performing stretch-and-fold on bubbly fermented sourdough dough on flour-dusted marble counter, warm morning bakery light, 8k"
            elif any(k in combined_context for k in ["score", "steam", "dutch oven", "bake"]):
                return "Baker scoring artisan sourdough dough loaf with razor blade lame before sliding into preheated Dutch oven, 8k"
            else:
                return "Golden brown artisan sourdough bread loaf with crackling blistered crust and dramatic scoring ear, sliced open revealing airy open crumb, 8k"
        elif domain == "pets":
            if any(k in combined_context for k in ["reward", "treat", "marker", "click"]):
                return "Close-up of happy golden retriever dog making eye contact and receiving high-value training treat, bright sunny park, 8k"
            elif any(k in combined_context for k in ["distract", "outdoor", "leash", "walk"]):
                return "Well-mannered dog walking politely on loose leash beside handler through vibrant green outdoor park, natural lighting"
            else:
                return "Happy alert dog sitting attentively on grass looking up with joyful expression, 8k National Geographic documentary photography"
        elif domain == "space":
            if any(k in combined_context for k in ["trajectory", "launch", "rocket", "orbit"]):
                return "Dramatic orbital view of spacecraft rocket accelerating with glowing blue plasma thrusters against deep starry cosmos, 8k"
            elif any(k in combined_context for k in ["telescope", "observatory", "deep space", "galaxy"]):
                return "Breathtaking deep space James Webb telescope view of colorful glowing cosmic nebula and spiral galaxies, 8k"
            elif any(k in combined_context for k in ["mars", "rover", "planet", "surface"]):
                return "Robotic planetary rover on red rocky Mars landscape with robotic arm analyzing stone, distant dusty mountain horizon, 8k"
            else:
                return f"Inspiring cinematic view of planet Earth from orbit with volumetric sun rays illuminating the atmospheric blue rim, 8k"
        elif domain == "gardening":
            if any(k in combined_context for k in ["soil", "compost", "plant", "seedling"]):
                return "Gardener hands wearing canvas gloves planting young green tomato seedling into rich dark organic compost with hand trowel, 8k"
            elif any(k in combined_context for k in ["water", "irrigation", "morning"]):
                return "Water droplets glistening on vibrant green vegetable leaves from gentle morning watering can spray, soft sunlight, 8k"
            else:
                return "Thriving lush backyard garden filled with blooming flowers, fresh herbs, and climbing vines in warm golden afternoon sunlight, 8k"
        elif domain == "back_pain":
            if any(k in combined_context for k in ["decompress", "stretch", "lumbar", "spine"]):
                return "Person performing gentle restorative spinal decompression stretch on yoga mat, bright tranquil natural wood studio, 8k"
            elif any(k in combined_context for k in ["glute", "bridge", "core", "activate"]):
                return "Athletic person performing proper glute bridge activation exercise on mat with aligned neutral pelvis, soft studio light, 8k"
            else:
                return "Person standing tall with relaxed healthy posture and open shoulders outdoors in fresh morning sunlight, feeling revitalized, 8k"
        elif domain == "coding":
            if any(k in combined_context for k in ["debug", "test", "syntax", "code"]):
                return "Curved ultrawide computer monitor displaying clean colorful Python code syntax in dark-themed IDE, mechanical keyboard glowing, 8k"
            elif any(k in combined_context for k in ["type", "hands", "keyboard"]):
                return "Close-up shot of software developer hands typing rapidly on mechanical keyboard with warm desk lamp and coffee cup, 8k"
            else:
                return "Modern software engineer dual-monitor desk setup in quiet modern office overlooking city at night, clean development environment, 8k"
        elif domain == "culinary":
            if phase == "intro":
                return f"Cinematic close-up establishing shot of {clean}, steam rising, warm ambient café lighting, shallow depth of field, 8k resolution, photorealistic"
            elif phase == "mechanism":
                return f"Detailed macro action shot demonstrating the preparation and fine details of {clean}, stainless steel tools, studio lighting"
            elif phase == "detail":
                return f"Ultra high definition close-up of {clean} in active process, rich textures, vibrant tones, magazine cover photography"
            else:
                return f"Artisan presentation of finished {clean} on rustic wooden table, soft backlight, beautiful composition"
        elif domain == "technology":
            if phase == "intro":
                return f"Futuristic cinematic wide shot representing {clean}, glowing holographic data interfaces, sleek server room, volumetric blue and purple neon lighting, 8k"
            elif phase == "mechanism":
                return f"Intricate macro shot of advanced microchip architecture and glowing fiber optics illustrating {clean}, precision engineering"
            elif phase == "detail":
                return f"Modern tech developer workstation with multiple monitors displaying data workflows of {clean}, soft ambient lighting"
            else:
                return f"Inspiring high-tech laboratory with engineers collaborating on {clean}, bright futuristic aesthetic, cinematic render"
        elif domain == "science":
            if phase == "intro":
                return f"Breathtaking cinematic wide shot showcasing {clean} in nature, dramatic volumetric sunbeams breaking through, 8k National Geographic photography"
            elif phase == "mechanism":
                return f"Scientific microscopic close-up revealing cellular and molecular interactions of {clean}, vibrant natural colors, ultra-detailed"
            elif phase == "detail":
                return f"Time-lapse view capturing dynamic natural processes of {clean}, rich organic textures, golden hour sunlight"
            else:
                return f"Inspiring panoramic landscape celebrating the environmental impact of {clean}, clear blue sky, vivid hyperrealistic scenery"
        elif domain == "wellness":
            if phase == "intro":
                return f"Serene morning aesthetic shot illustrating {clean}, sunlit minimalist studio, warm natural tones, peaceful atmosphere, 8k"
            elif phase == "mechanism":
                return f"Action shot showing proper alignment and focused breathing during {clean}, soft cinematic lighting, professional athletic posture"
            elif phase == "detail":
                return f"Close-up of mindful execution and energy during {clean}, clean modern studio backdrop, sharp focus"
            else:
                return f"Energized, healthy person enjoying vibrant outdoor vitality after practicing {clean}, golden sunrise, uplifting cinematic view"
        elif domain == "finance":
            if phase == "intro":
                return f"Sleek modern boardroom overlooking financial district skyline, representing {clean}, cinematic glass reflections, premium corporate lighting, 8k"
            elif phase == "mechanism":
                return f"High-resolution interactive digital market graphs and investment metrics displaying exponential growth for {clean}, clean modern UI"
            elif phase == "detail":
                return f"Professional businesswoman analyzing strategic portfolios and {clean} forecasts, modern minimalist office"
            else:
                return f"Inspiring wide shot symbolizing long-term financial success and freedom through {clean}, bright aspirational sunset backdrop"
        elif domain == "history":
            if phase == "intro":
                return f"Epic cinematic establishing shot of historical monuments and ancient setting of {clean}, dramatic stormy sky, cinematic film grain, 8k"
            elif phase == "mechanism":
                return f"Detailed historical artifacts, ancient scrolls, and architectural craftsmanship related to {clean}, warm candlelight"
            elif phase == "detail":
                return f"Atmospheric recreation of key historical decision scene regarding {clean}, authentic period costumes, dramatic chiaroscuro lighting"
            else:
                return f"Majestic panoramic view of historical landmark of {clean} standing through centuries, warm golden hour, timeless heritage"
        elif domain == "wildlife":
            if phase == "intro":
                return f"Dramatic cinematic establishing shot of majestic wild animals in natural habitat illustrating {clean}, golden hour, National Geographic 8k"
            elif phase == "mechanism":
                return f"Intense close-up action shot capturing animal agility, primal survival instincts, and muscular movement in the wild"
            elif phase == "detail":
                return f"Detailed documentary photography capturing animal anatomy, predatory focus, and wilderness environment"
            else:
                return f"Powerful cinematic portrait of wildlife standing proud against dramatic mountain sunset, 8k resolution"
        else:
            if phase == "intro":
                return f"Striking cinematic establishing shot setting the stage for {clean}, dramatic lighting, 8k resolution, sharp focus"
            elif phase == "mechanism":
                return f"Detailed action close-up demonstrating core process and breakdown of {clean}, vibrant studio lighting, hyperrealistic"
            elif phase == "detail":
                return f"Macro detailed shot highlighting intricate textures, components, and key elements of {clean}, shallow depth of field"
            elif phase == "application":
                return f"Dynamic real-world context scene illustrating practical impact and execution of {clean}, cinematic composition"
            else:
                return f"Inspiring wide-angle panoramic view capturing the ultimate significance and future of {clean}, golden hour cinematography"

    # -------------------------------------------------------------
    # TOPIC-SPECIFIC STRATEGY FALLBACK
    # -------------------------------------------------------------
    def _generate_topic_specific_strategy(self, topic: str, audience: str, platform: str, duration: int, goal: str, tone: str) -> dict:
        clean = self._clean_topic_name(topic)
        lower = topic.lower()
        scenes_count = max(3, min(8, int(duration // 10) or 5))

        def _match(pattern: str) -> bool:
            return bool(re.search(r'\b(' + pattern + r')\b', lower))

        if _match(r'pizza\w*'):
            titles = [
                f"The Artisan Secret to Perfect {clean}",
                f"How to Master {clean} at Home",
                f"The Fundamentals of Authentic {clean}"
            ]
            hooks = [
                f"The single biggest mistake in homemade {clean} isn't the toppings—it's rushing the fermentation.",
                f"If you want Neapolitan pizzeria quality {clean} at home, this is the exact principle that changes everything.",
                f"Most people think great {clean} requires an expensive oven, but the real secret happens 48 hours before baking."
            ]
        elif _match(r'espresso|coffee|brew\w*|barista|sourdough|bread|baking|bake|cook\w*|recipe\w*|chef|pasta\w*|dish\w*|food'):
            titles = [
                f"The Secret Technique for Exceptional {clean}",
                f"How to Master {clean} Like a Professional",
                f"The Critical Fundamentals of {clean}"
            ]
            hooks = [
                f"Professional culinary masters know that exceptional {clean} comes down to precise temperature and timing control.",
                f"Most home cooks struggle with {clean} because they skip this one foundational technique.",
                f"If you want restaurant-grade {clean} every single time, here is the exact formula that works."
            ]
        elif _match(r'habit\w*|routine\w*|morning\w*|productivity|focus|discipline|procrastinat\w*'):
            titles = [
                f"5 Daily Habits That Transform Your Focus",
                f"The High-Performance Routine for {clean}",
                f"How Small Daily Choices in {clean} Compound Into Massive Results"
            ]
            hooks = [
                f"How you spend the first thirty minutes after waking programs your mental focus for the entire day.",
                f"High performers don't rely on endless willpower—they design frictionless daily systems.",
                f"If you want effortless consistency with {clean}, the secret is removing friction before you even start."
            ]
        elif _match(r'cyber\w*|security|hack\w*|phish\w*|vpn|malware|auth\w*|mfa'):
            titles = [
                f"The Hidden Security Architecture of {clean}",
                f"How to Protect Your Digital Footprint with {clean}",
                f"The Essential Defense Protocol for {clean}"
            ]
            hooks = [
                f"Over ninety percent of digital breaches happen through simple human error before a single system is hacked.",
                f"The biggest vulnerability in modern {clean} isn't sophisticated zero-days—it's unpatched default settings.",
                f"Protecting your sensitive data with {clean} comes down to three non-negotiable security layers."
            ]
        elif _match(r'fitness|workout\w*|exercise\w*|back\s+pain|pain|yoga|health|muscle\w*|running|stretching'):
            titles = [
                f"The Science-Backed Approach to {clean}",
                f"How to Relieve {clean} With Smart Mechanics",
                f"The Daily Movement Protocol for {clean}"
            ]
            hooks = [
                f"Prolonged sitting tightens your hip flexors, pulling on your lower spine and triggering persistent tension.",
                f"Real physical progress with {clean} isn't about training to exhaustion—it's about stimulus and targeted recovery.",
                f"If you want lasting relief from {clean}, addressing joint mobility first is what makes exercises actually work."
            ]
        elif _match(r'ai|artificial\s+intelligence|machine\s+learning|coding|python|software|algorithm\w*|tech'):
            titles = [
                f"Understanding {clean}: The Complete Breakdown",
                f"How {clean} Actually Works Behind the Scenes",
                f"The Core Architecture of Modern {clean}"
            ]
            hooks = [
                f"Behind the hype of {clean} lies an elegant algorithmic pipeline that solves complex problems in milliseconds.",
                f"Most developers struggle with {clean} because they jump straight to advanced tools before mastering data fundamentals.",
                f"The real breakthrough in {clean} comes down to low latency, clean architecture, and scalable models."
            ]
        elif _match(r'money|invest\w*|finance|stocks?|wealth|business|crypto|real\s+estate'):
            titles = [
                f"The Wealth-Building Truth About {clean}",
                f"Strategic Principles for Mastering {clean}",
                f"The 3 Rules of Long-Term Success in {clean}"
            ]
            hooks = [
                f"The most dangerous trap in {clean} isn't taking calculated risks—it's letting inflation quietly erode your capital.",
                f"True financial growth in {clean} is driven by compounding returns and disciplined risk management over time.",
                f"Before investing a single dollar in {clean}, understanding your risk-reward ratio is what keeps you profitable."
            ]
        elif "how to" in clean.lower():
            titles = [
                f"{clean}: Step-by-Step Breakdown",
                f"How to Master {clean} Fast",
                f"The Essential Blueprint for {clean}"
            ]
            hooks = [
                f"Mastering {clean} becomes simple once you break it down into these exact sequential steps.",
                f"If you've been struggling to master {clean}, this practical formula eliminates all the guesswork.",
                f"Here is the exact step-by-step breakdown you need to achieve consistent success with {clean}."
            ]
        else:
            titles = [
                f"The Essential Principles of {clean}",
                f"Mastering {clean}: The Practical Breakdown",
                f"The Counterintuitive Truth About {clean}",
                f"How to Achieve Consistent Results With {clean}"
            ]
            hooks = [
                f"When it comes to {clean}, the smallest adjustment in your approach often creates the most noticeable breakthrough.",
                f"Most people struggle with {clean} because they try to optimize everything at once instead of mastering one step.",
                f"To achieve consistent results in {clean}, you need a repeatable workflow that eliminates unnecessary friction.",
                f"Here is the counterintuitive reality of {clean} that completely changes how you approach it."
            ]

        idx = abs(hash(clean)) % len(titles)
        title = titles[idx]
        hook = hooks[idx]

        return {
            "title": title,
            "hook": hook,
            "recommended_duration": duration,
            "style": f"High-Retention Cinematic {tone}",
            "scenes_count": scenes_count,
            "voice_style": "Professional Male",
            "caption_style": "Bold Highlight",
            "cta": f"Follow for more in-depth breakdowns on {clean} and save this video for later!"
        }

    # -------------------------------------------------------------
    # TOPIC-SPECIFIC SOCIAL POST FALLBACK
    # -------------------------------------------------------------
    def _generate_topic_specific_social_post(self, topic: str, title: str, hook: str, platform: str, audience: str, goal: str, tone: str) -> dict:
        clean = self._clean_topic_name(topic)
        display_title = title or clean
        words = re.findall(r'[a-zA-Z0-9]+', clean)
        topic_tags = [f"#{w.capitalize()}" for w in words if len(w) > 2 and w.lower() not in ["the", "and", "for", "with", "about", "how", "why", "what"]]
        
        all_tags = topic_tags + ["#Shorts", "#Viral", "#Education", "#DidYouKnow", "#LearnOnTikTok"]
        hashtags = list(dict.fromkeys(all_tags))[:12]
        hashtags_str = " ".join(hashtags)

        caption = f"""🔥 {hook or ('Everything you need to know about ' + clean)}

Here is the breakdown of {display_title}:
💡 Understanding the fundamental mechanics
⚙️ How to execute with precision and consistency
🚀 Why this matters for your long-term success

Drop your thoughts below and follow for more daily insights! 👇

{hashtags_str}"""

        return {
            "caption": caption.strip(),
            "short_caption": f"Everything you need to know about {clean} in 60 seconds! 🔥 {hashtags_str}",
            "call_to_action": f"Save this post and share it with someone interested in {clean}!",
            "hashtags": hashtags,
            "hashtags_string": hashtags_str,
            "platform_variations": {
                "youtube_shorts": f"{display_title}\n\n{hook}\n\nSubscribe for more breakdowns!\n{hashtags_str}",
                "instagram_reels": f"✨ {display_title}\n\n{hook}\n\nSave this reel for later! 📌\n\n{hashtags_str}",
                "tiktok": f"{hook} Watch until the end for the key takeaway! 🔥 #fyp {hashtags_str}",
                "linkedin": f"Deep Dive: {display_title}\n\nKey takeaway: Mastering {clean} comes down to understanding core fundamentals.\n\nWhat has been your experience? Let's discuss in the comments."
            },
            "engagement_question": f"What is your biggest question or experience with {clean}? Let's discuss in the comments! 👇"
        }

    # -------------------------------------------------------------
    # DATA VALIDATION & CLEANING
    # -------------------------------------------------------------
    def _validate_strategy_data(self, data: dict) -> bool:
        if not isinstance(data, dict):
            return False
        title = data.get("title", "")
        hook = data.get("hook", "")
        return bool(title and hook and len(title.strip()) > 3 and len(hook.strip()) > 5)

    def _validate_script_data(self, data: dict) -> bool:
        if not isinstance(data, dict):
            return False
        scenes = data.get("scenes")
        if not scenes or not isinstance(scenes, list) or len(scenes) == 0:
            return False
        first_scene = scenes[0]
        narration = first_scene.get("narration", "")
        visual = first_scene.get("visual_description", "")
        return bool(narration and visual and len(narration.strip()) > 10)

    def _clean_script_data(self, data: dict, topic: str, strategy: dict, duration: int, scenes_count: int) -> dict:
        """Ensures all script scenes have proper durations, scene_ids, and non-empty narrations."""
        scenes = data.get("scenes", [])
        scene_duration = round(duration / max(1, len(scenes)), 1)
        cleaned_scenes = []
        for idx, sc in enumerate(scenes, 1):
            cleaned_scenes.append({
                "scene_id": idx,
                "duration": sc.get("duration", scene_duration) or scene_duration,
                "narration": sc.get("narration", f"Scene {idx} exploring {topic}.").strip(),
                "visual_description": sc.get("visual_description", f"Cinematic shot illustrating {topic}").strip(),
                "on_screen_text": sc.get("on_screen_text", f"Point {idx}").strip(),
                "transition": sc.get("transition", "fade")
            })
        
        return {
            "title": data.get("title") or strategy.get("title") or topic,
            "hook": data.get("hook") or strategy.get("hook") or f"Important facts about {topic}.",
            "audience": data.get("audience", "General Audience"),
            "goal": data.get("goal", "Educate"),
            "tone": data.get("tone", "Educational"),
            "platform": data.get("platform", "YouTube Shorts"),
            "duration": duration,
            "scenes": cleaned_scenes,
            "cta": data.get("cta") or strategy.get("cta") or "Follow for more!"
        }

    def _validate_social_post_data(self, data: dict) -> bool:
        if not isinstance(data, dict):
            return False
        caption = data.get("caption", "")
        return bool(caption and len(caption.strip()) > 20 and (data.get("hashtags") or data.get("hashtags_string")))

    def _format_social_post_data(self, data: dict, clean_topic: str) -> dict:
        raw_hashtags = data.get("hashtags", [])
        if isinstance(raw_hashtags, str):
            raw_hashtags = [h.strip() for h in raw_hashtags.split() if h.startswith("#")]
        
        hashtags = []
        for h in raw_hashtags:
            if not isinstance(h, str):
                continue
            cleaned = re.sub(r'[^\w#]', '', h.strip())
            if not cleaned:
                continue
            if not cleaned.startswith("#"):
                cleaned = f"#{cleaned}"
            if cleaned not in hashtags:
                hashtags.append(cleaned)
        
        if not hashtags:
            for w in clean_topic.split():
                clean_w = re.sub(r'[^\w]', '', w.capitalize())
                if len(clean_w) > 2:
                    hashtags.append(f"#{clean_w}")
            hashtags.extend(["#Shorts", "#Viral", "#Trending"])

        hashtags_string = data.get("hashtags_string") or " ".join(hashtags)
        platform_variations = data.get("platform_variations") or {}
        if not isinstance(platform_variations, dict):
            platform_variations = {}

        return {
            "caption": data.get("caption", ""),
            "short_caption": data.get("short_caption", ""),
            "call_to_action": data.get("call_to_action", "Save & share this video!"),
            "hashtags": hashtags,
            "hashtags_string": hashtags_string,
            "platform_variations": {
                "youtube_shorts": platform_variations.get("youtube_shorts", data.get("caption", "")),
                "instagram_reels": platform_variations.get("instagram_reels", data.get("caption", "")),
                "tiktok": platform_variations.get("tiktok", data.get("caption", "")),
                "linkedin": platform_variations.get("linkedin", data.get("caption", ""))
            },
            "engagement_question": data.get("engagement_question", "What did you think of this? Drop a comment below! 👇")
        }

    def _clean_topic_name(self, topic: str) -> str:
        clean = topic.strip().rstrip(".!?")
        if "\n" in clean:
            clean = clean.split("\n")[0].strip()
        if len(clean) > 70:
            first_sent = re.split(r'[.!?]', clean)[0].strip()
            if 10 < len(first_sent) <= 70:
                clean = first_sent
            else:
                clean = clean[:65].rsplit(" ", 1)[0]
        if clean.islower():
            clean = clean.title()
        return clean

llm_service = LLMService()
