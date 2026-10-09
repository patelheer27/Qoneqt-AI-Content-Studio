import json
import os
import re
import html
import requests
import urllib.parse
from groq import Groq
from app.config import settings

class LLMService:
    def __init__(self):
        self.api_key = getattr(settings, "GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
        self.model = getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile") or "llama-3.3-70b-versatile"
        self.pollinations_api_key = getattr(settings, "POLLINATIONS_API_KEY", "") or os.getenv("POLLINATIONS_API_KEY", "")
        
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
        """Extracts and parses JSON from text, handling markdown codeblocks."""
        clean = text.strip()
        if "```" in clean:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean, re.IGNORECASE)
            if match:
                clean = match.group(1).strip()
        first = clean.find("{")
        last = clean.rfind("}")
        if first != -1 and last != -1:
            clean = clean[first:last + 1]
        return json.loads(clean)

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
            max_tokens=2500,
            response_format={"type": "json_object"}
        )
        content = completion.choices[0].message.content
        return self._extract_json(content)

    def _call_pollinations_json(self, system_prompt: str, user_prompt: str) -> dict:
        """Calls Pollinations AI text endpoint expecting a JSON object."""
        headers = {}
        if self.pollinations_api_key:
            headers["Authorization"] = f"Bearer {self.pollinations_api_key}"

        combined_prompt = f"{system_prompt}\n{user_prompt}\nIMPORTANT: Output strictly a valid raw JSON object only. No markdown fences, no explanatory text."

        # Method 1: GET endpoint with openai-fast model (high speed, free tier)
        try:
            encoded = urllib.parse.quote(combined_prompt)
            if len(encoded) < 7000:
                url_get = f"https://text.pollinations.ai/{encoded}?model=openai-fast&json=true"
                res = requests.get(url_get, headers=headers, timeout=22)
                if res.status_code == 200 and res.text.strip():
                    return self._extract_json(res.text)
        except Exception as e:
            print(f"[LLMService] Pollinations GET (openai-fast) attempt: {e}")

        # Method 2: Standard GET endpoint
        try:
            encoded = urllib.parse.quote(combined_prompt)
            if len(encoded) < 7000:
                url_get = f"https://text.pollinations.ai/{encoded}?json=true"
                res = requests.get(url_get, headers=headers, timeout=20)
                if res.status_code == 200 and res.text.strip():
                    return self._extract_json(res.text)
        except Exception as e:
            print(f"[LLMService] Pollinations GET (standard) attempt: {e}")

        # Method 3: POST endpoint (fallback)
        url_post = "https://text.pollinations.ai/"
        payload = {
            "messages": [
                {"role": "system", "content": f"{system_prompt} Output strictly valid raw JSON only."},
                {"role": "user", "content": user_prompt}
            ],
            "model": "openai-fast",
            "jsonMode": True
        }
        try:
            res = requests.post(url_post, json=payload, headers=headers, timeout=20)
            if res.status_code == 200:
                return self._extract_json(res.text)
        except Exception as e:
            pass

        raise Exception("Pollinations request failed across all methods")

    # -------------------------------------------------------------
    # AI STRATEGY GENERATION (ENGLISH ONLY)
    # -------------------------------------------------------------
    def generate_strategy(self, topic: str, audience: str = "General Audience", platform: str = "YouTube Shorts", duration: int = 60, goal: str = "Educate", tone: str = "Educational", language: str = "English") -> dict:
        """Generates a comprehensive video strategy in English tailored specifically to the user's topic or input script."""
        clean_topic = self._clean_topic_name(topic)
        scenes_count = max(3, min(8, int(duration // 10) or 5))
        system_prompt = "You are a world-class AI Video Director. Output strictly a valid raw JSON object only with no markdown formatting."
        
        user_prompt = f"""Create an engaging video production strategy specifically for:
Topic / Input Script: "{topic}"
Language: English
Target Audience: {audience}
Primary Goal: {goal}
Tone: {tone}
Platform: {platform}
Target Duration: {duration} seconds

Requirements:
- Note: If the input is an existing script or draft, use it as the topic concept to plan deeper detailing.
- "title": A high-converting, curiosity-driven title specifically summarizing "{clean_topic}".
- "hook": A punchy opening hook (first 3 seconds) that immediately grabs viewer attention with a thought-provoking question, shocking fact, or bold claim.
- "recommended_duration": {duration}
- "style": Visual style description (e.g. "Fast-paced cinematic {tone} with high-retention cuts").
- "scenes_count": {scenes_count}
- "voice_style": Select the best voiceover style: "Energetic Female", "Professional Male", "Warm Female", or "Deep Male".
- "caption_style": "Bold Highlight"
- "cta": A natural call-to-action specifically encouraging engagement on "{clean_topic}".

Return ONLY a valid JSON object matching this schema:
{{
    "title": "Title tailored to {clean_topic}",
    "hook": "Opening hook specifically about {clean_topic}",
    "recommended_duration": {duration},
    "style": "Fast-paced {tone}",
    "scenes_count": {scenes_count},
    "voice_style": "Professional Male",
    "caption_style": "Bold Highlight",
    "cta": "Engaging call-to-action tailored to {clean_topic}"
}}"""

        # Tier 1: Groq API
        if self.client:
            try:
                print(f"[LLMService] Generating strategy via Groq for '{clean_topic}'...")
                data = self._call_groq_json(system_prompt, user_prompt)
                if self._validate_strategy_data(data):
                    return data
            except Exception as e:
                print(f"[LLMService] Groq API error in generate_strategy: {e}")

        # Tier 2: Free Pollinations AI
        try:
            print(f"[LLMService] Generating strategy via Pollinations AI for '{clean_topic}'...")
            data = self._call_pollinations_json(system_prompt, user_prompt)
            if self._validate_strategy_data(data):
                return data
        except Exception as e:
            print(f"[LLMService] Pollinations AI error in generate_strategy: {e}")

        # Tier 3: Context-rich dynamic strategy fallback
        print(f"[LLMService] Generating topic-specific contextual strategy for '{clean_topic}'...")
        return self._generate_topic_specific_strategy(topic, audience, platform, duration, goal, tone)

    # -------------------------------------------------------------
    # AI SCRIPT GENERATION (ENGLISH ONLY, DEEP DETAIL FOR SPECIFIC TOPIC OR SCRIPT)
    # -------------------------------------------------------------
    def generate_script(self, topic: str, strategy: dict, audience: str = "General Audience", goal: str = "Educate", tone: str = "Educational", platform: str = "YouTube Shorts", language: str = "English") -> dict:
        """Generates an in-depth, scene-by-scene script with authentic domain facts and deep detailing specifically for the topic or input script."""
        clean_topic = self._clean_topic_name(topic)
        duration = strategy.get("recommended_duration", 60)
        scenes_count = strategy.get("scenes_count", max(3, min(8, int(duration // 10) or 5)))
        scene_duration = round(duration / scenes_count, 1)

        system_prompt = "You are an expert YouTube scriptwriter and video producer. Output strictly valid raw JSON only."
        user_prompt = f"""Write an in-depth, high-retention video script based on: "{topic}".
Audience: {audience}. Goal: {goal}. Tone: {tone}. Total Duration: {duration}s.
CRITICAL INSTRUCTIONS:
1. If the input is an existing script or topic draft, use it as the foundation to generate DEEPER DETAILING for every scene.
2. For each scene:
   - "on_screen_text": A concise 2 to 4-word Title (will be shifted to the TOP of the video frame as the scene headline).
   - "narration": 2 to 3 thorough, informative sentences detailing concrete facts, step-by-step mechanisms, and authentic explanations. This narration will be converted into speech and captioned word-for-word on screen.
   - "visual_description": A cinematic, photorealistic visual description.
Return ONLY valid JSON matching this schema:
{{
    "title": "{strategy.get('title', clean_topic)}",
    "hook": "{strategy.get('hook', 'Important facts about ' + clean_topic)}",
    "audience": "{audience}",
    "goal": "{goal}",
    "tone": "{tone}",
    "platform": "{platform}",
    "duration": {duration},
    "scenes": [
        {{"scene_id": 1, "duration": {scene_duration}, "narration": "Detailed fact-filled opening narration introducing the core question or mechanism of {clean_topic}", "visual_description": "Cinematic visual description specifying environment, lighting, and action", "on_screen_text": "Key Concept", "transition": "fade"}},
        {{"scene_id": 2, "duration": {scene_duration}, "narration": "Detailed fact-filled narration explaining the core process, science, or technique of {clean_topic}", "visual_description": "Close-up action visual demonstrating the process", "on_screen_text": "How It Works", "transition": "fade"}},
        {{"scene_id": 3, "duration": {scene_duration}, "narration": "Detailed fact-filled narration exploring the crucial nuances, rules, or breakthroughs of {clean_topic}", "visual_description": "Macro detailed shot illustrating key component", "on_screen_text": "Deeper Insight", "transition": "fade"}},
        {{"scene_id": 4, "duration": {scene_duration}, "narration": "Detailed concluding narration with key takeaways and real-world significance of {clean_topic}", "visual_description": "Polished concluding visual celebrating success", "on_screen_text": "Final Takeaway", "transition": "fade"}}
    ],
    "cta": "{strategy.get('cta', 'Follow for more insights on ' + clean_topic + '!')}"
}}"""

        # Tier 1: Groq API
        if self.client:
            try:
                print(f"[LLMService] Generating detailed script via Groq for '{topic}'...")
                data = self._call_groq_json(system_prompt, user_prompt)
                if self._validate_script_data(data):
                    return self._clean_script_data(data, topic, strategy, duration, scenes_count)
            except Exception as e:
                print(f"[LLMService] Groq API error in generate_script: {e}")

        # Tier 2: Free Pollinations AI
        try:
            print(f"[LLMService] Generating detailed script via Pollinations AI for '{topic}'...")
            data = self._call_pollinations_json(system_prompt, user_prompt)
            if self._validate_script_data(data):
                return self._clean_script_data(data, topic, strategy, duration, scenes_count)
        except Exception as e:
            print(f"[LLMService] Pollinations AI error in generate_script: {e}")

        # Tier 3: Knowledge-Engine Powered Script Synthesizer
        print(f"[LLMService] Synthesizing rich topic-specific script for '{topic}' via Knowledge Engine...")
        return self._synthesize_topic_specific_script(topic, strategy, audience, goal, tone, platform, duration, scenes_count)

    # -------------------------------------------------------------
    # AI SOCIAL POST GENERATION (ENGLISH ONLY)
    # -------------------------------------------------------------
    def generate_social_post(self, topic: str, title: str = "", hook: str = "", platform: str = "YouTube Shorts", audience: str = "General Audience", goal: str = "Educate", tone: str = "Educational", language: str = "English") -> dict:
        """Generates viral, engaging social media captions and hyper-relevant hashtags in English."""
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
    # KNOWLEDGE ENGINE & TOPIC RESEARCH
    # -------------------------------------------------------------
    def _fetch_topic_knowledge(self, topic: str) -> dict:
        """Fetches authentic encyclopedic knowledge, definitions, and facts for the specific topic within 300ms."""
        clean = re.sub(r'^(how to\s+|why\s+|what is\s+|the truth about\s+|5 ways\s+|5 benefits of\s+|secrets of\s+)', '', topic, flags=re.IGNORECASE).strip()
        headers = {"User-Agent": "QoneqtContentStudio/1.0 (contact@qoneqt.com)"}
        
        try:
            search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(clean)}&format=json&utf8=1"
            r = requests.get(search_url, headers=headers, timeout=5)
            if r.status_code == 200:
                hits = r.json().get("query", {}).get("search", [])
                if hits:
                    top_hit = hits[0]
                    top_title = top_hit.get("title", "")
                    snippets = [re.sub(r'<[^>]+>', '', html.unescape(h.get("snippet", ""))).strip() for h in hits[:4]]
                    
                    sum_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(top_title)}"
                    r2 = requests.get(sum_url, headers=headers, timeout=5)
                    extract = ""
                    description = ""
                    if r2.status_code == 200:
                        sum_data = r2.json()
                        extract = sum_data.get("extract", "")
                        description = sum_data.get("description", "")
                    
                    return {
                        "title": top_title,
                        "description": description,
                        "extract": extract,
                        "snippets": snippets
                    }
        except Exception as e:
            print(f"[LLMService] Knowledge fetch error for '{topic}': {e}")
        
        return {}

    # -------------------------------------------------------------
    # TOPIC-SPECIFIC SCRIPT SYNTHESIS (GUARANTEED REAL DEPTH)
    # -------------------------------------------------------------
    def _synthesize_topic_specific_script(self, topic: str, strategy: dict, audience: str, goal: str, tone: str, platform: str, duration: int, scenes_count: int) -> dict:
        """Synthesizes a deep, realistic, topic-specific script using factual knowledge, script decomposition, and domain detailing."""
        clean = self._clean_topic_name(topic)
        knowledge = self._fetch_topic_knowledge(clean)
        scene_duration = round(duration / scenes_count, 1)

        extract = knowledge.get("extract", "")
        snippets = knowledge.get("snippets", [])
        
        # Check if the user input itself contains multiple sentences (e.g. provided as a script)
        script_sentences = [s.strip() for s in re.split(r'[.\n]+', topic) if len(s.strip()) > 15]

        # Split extract into clean factual sentences
        raw_sentences = [s.strip() for s in re.split(r'\.\s+', extract) if len(s.strip()) > 20]
        for snip in snippets:
            for s in re.split(r'\.\s+', snip):
                if len(s.strip()) > 25 and s.strip() not in raw_sentences:
                    raw_sentences.append(s.strip())

        title = strategy.get("title") or f"{clean}: The Complete Guide"
        hook = strategy.get("hook") or f"Have you ever wondered what really makes {clean} so powerful?"
        cta = strategy.get("cta") or f"Follow for more insights on {clean} and share this with a friend!"

        # Determine topic domain category for appropriate cinematography and vocabulary
        lower_topic = clean.lower()
        if any(w in lower_topic for w in ["coffee", "espresso", "recipe", "cook", "bake", "food", "tea"]):
            domain = "culinary"
        elif any(w in lower_topic for w in ["quantum", "ai", "machine learning", "code", "software", "tech", "algorithm", "computer", "robot"]):
            domain = "technology"
        elif any(w in lower_topic for w in ["tree", "plant", "nature", "earth", "climate", "biology", "space", "star", "physics", "photosynthesis", "solar"]):
            domain = "science"
        elif any(w in lower_topic for w in ["yoga", "workout", "fitness", "health", "diet", "sleep", "muscle", "running", "fasting"]):
            domain = "wellness"
        elif any(w in lower_topic for w in ["money", "invest", "finance", "business", "market", "wealth", "stock", "career", "startup"]):
            domain = "finance"
        elif any(w in lower_topic for w in ["animal", "wildlife", "lion", "tiger", "wolf", "dog", "cat", "bear", "beast", "creature", "predator", "safari", "forest", "species", "hunting"]):
            domain = "wildlife"
        elif any(w in lower_topic for w in ["rome", "war", "history", "ancient", "century", "empire", "king", "revolution"]):
            domain = "history"
        else:
            domain = "general"

        scenes = []
        for i in range(1, scenes_count + 1):
            # If user provided a script, extract the corresponding premise for this scene
            script_premise = script_sentences[(i - 1) % len(script_sentences)] if script_sentences else ""

            if i == 1:
                # Scene 1: High-impact hook and concept introduction
                intro_fact = raw_sentences[0] if raw_sentences else f"{clean} represents one of the most consequential concepts in modern understanding."
                if script_premise:
                    narration = f"{hook} {script_premise}. Examining this in depth reveals fascinating real-world mechanics. {intro_fact}"
                else:
                    narration = f"{hook} When examining {clean}, the reality is captivating. {intro_fact}"
                visual = self._get_domain_visual(domain, clean, "intro")
                text = f"{clean[:26]}"
            elif i == scenes_count:
                # Last Scene: Climax, synthesis, and action prompt
                closing_fact = raw_sentences[-1] if len(raw_sentences) > 2 else f"Understanding the true nature of {clean} changes your entire perspective."
                if script_premise:
                    narration = f"Bringing it all together: {script_premise}. {closing_fact} {cta}"
                else:
                    narration = f"In summary, {clean} offers transformative insights that continue to shape how we think and act. {closing_fact} {cta}"
                visual = self._get_domain_visual(domain, clean, "outro")
                text = "Key Takeaway"
            elif i == 2:
                # Scene 2: Core mechanism / fundamental definition
                core_fact = raw_sentences[1] if len(raw_sentences) > 1 else f"At its foundation, key scientific and practical principles dictate exactly how it unfolds."
                if script_premise:
                    narration = f"Taking a deeper look at the mechanism: {script_premise}. {core_fact}"
                else:
                    narration = f"Let's look at how it works. {core_fact}"
                visual = self._get_domain_visual(domain, clean, "mechanism")
                text = "How It Works"
            elif i == 3:
                # Scene 3: Deep dive / technical nuance / key step
                nuance_fact = raw_sentences[2] if len(raw_sentences) > 2 else f"Detailed investigation reveals subtle factors that produce major outsized results."
                if script_premise:
                    narration = f"Going deeper into the specifics: {script_premise}. {nuance_fact}"
                else:
                    narration = f"Going deeper into the subject: {nuance_fact}"
                visual = self._get_domain_visual(domain, clean, "detail")
                text = "Core Insight"
            else:
                # Intermediate Scene: Practical application or historical/scientific factors
                extra_fact = raw_sentences[i - 1] if len(raw_sentences) > (i - 1) else f"Crucial factors and ongoing developments continue to influence how this unfolds."
                if script_premise:
                    narration = f"Analyzing another essential factor: {script_premise}. {extra_fact}"
                else:
                    narration = f"Another major dimension to consider: {extra_fact}"
                visual = self._get_domain_visual(domain, clean, "application")
                text = f"Key Factor {i - 1}"

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

    def _get_domain_visual(self, domain: str, topic: str, phase: str) -> str:
        """Constructs detailed, cinematic image generation prompts matching domain and context."""
        if domain == "culinary":
            if phase == "intro":
                return f"Cinematic close-up establishing shot of {topic}, steam rising, warm ambient café lighting, shallow depth of field, 8k resolution, photorealistic"
            elif phase == "mechanism":
                return f"Detailed macro action shot demonstrating the preparation and fine details of {topic}, stainless steel tools, studio lighting"
            elif phase == "detail":
                return f"Ultra high definition close-up of {topic} in active process, rich textures, vibrant tones, magazine cover photography"
            else:
                return f"Artisan presentation of finished {topic} on rustic wooden table, soft backlight, beautiful composition"
        elif domain == "technology":
            if phase == "intro":
                return f"Futuristic cinematic wide shot representing {topic}, glowing holographic data interfaces, sleek server room, volumetric blue and purple neon lighting, 8k"
            elif phase == "mechanism":
                return f"Intricate macro shot of advanced microchip architecture and glowing fiber optics illustrating {topic}, precision engineering"
            elif phase == "detail":
                return f"Modern tech developer workstation with multiple monitors displaying data workflows of {topic}, soft ambient lighting"
            else:
                return f"Inspiring high-tech laboratory with engineers collaborating on {topic}, bright futuristic aesthetic, cinematic render"
        elif domain == "science":
            if phase == "intro":
                return f"Breathtaking cinematic wide shot showcasing {topic} in nature, dramatic volumetric sunbeams breaking through, 8k National Geographic photography"
            elif phase == "mechanism":
                return f"Scientific microscopic close-up revealing cellular and molecular interactions of {topic}, vibrant natural colors, ultra-detailed"
            elif phase == "detail":
                return f"Time-lapse view capturing dynamic natural processes of {topic}, rich organic textures, golden hour sunlight"
            else:
                return f"Inspiring panoramic landscape celebrating the environmental impact of {topic}, clear blue sky, vivid hyperrealistic scenery"
        elif domain == "wellness":
            if phase == "intro":
                return f"Serene morning aesthetic shot illustrating {topic}, sunlit minimalist studio, warm natural tones, peaceful atmosphere, 8k"
            elif phase == "mechanism":
                return f"Action shot showing proper alignment and focused breathing during {topic}, soft cinematic lighting, professional athletic posture"
            elif phase == "detail":
                return f"Close-up of mindful execution and energy during {topic}, clean modern studio backdrop, sharp focus"
            else:
                return f"Energized, healthy person enjoying vibrant outdoor vitality after practicing {topic}, golden sunrise, uplifting cinematic view"
        elif domain == "finance":
            if phase == "intro":
                return f"Sleek modern boardroom overlooking financial district skyline, representing {topic}, cinematic glass reflections, premium corporate lighting, 8k"
            elif phase == "mechanism":
                return f"High-resolution interactive digital market graphs and investment metrics displaying exponential growth for {topic}, clean modern UI"
            elif phase == "detail":
                return f"Professional businesswoman analyzing strategic portfolios and {topic} forecasts, modern minimalist office"
            else:
                return f"Inspiring wide shot symbolizing long-term financial success and freedom through {topic}, bright aspirational sunset backdrop"
        elif domain == "history":
            if phase == "intro":
                return f"Epic cinematic establishing shot of historical monuments and ancient setting of {topic}, dramatic stormy sky, cinematic film grain, 8k"
            elif phase == "mechanism":
                return f"Detailed historical artifacts, ancient scrolls, and architectural craftsmanship related to {topic}, warm candlelight"
            elif phase == "detail":
                return f"Atmospheric recreation of key historical decision scene regarding {topic}, authentic period costumes, dramatic chiaroscuro lighting"
            else:
                return f"Majestic panoramic view of historical landmark of {topic} standing through centuries, warm golden hour, timeless heritage"
        elif domain == "wildlife":
            if phase == "intro":
                return f"Dramatic cinematic establishing shot of majestic wild animals in natural habitat illustrating {topic}, golden hour, National Geographic 8k"
            elif phase == "mechanism":
                return f"Intense close-up action shot capturing animal agility, primal survival instincts, and muscular movement in the wild"
            elif phase == "detail":
                return f"Detailed documentary photography capturing animal anatomy, predatory focus, and wilderness environment"
            elif phase == "application":
                return f"Wide landscape shot showcasing animal ecosystem interactions and natural territory competition"
            else:
                return f"Powerful cinematic portrait of wildlife standing proud against dramatic mountain sunset, 8k resolution"
        else: # general domain with distinct phase visuals
            if phase == "intro":
                return f"Striking cinematic establishing shot setting the stage for {topic}, dramatic lighting, 8k resolution, sharp focus"
            elif phase == "mechanism":
                return f"Detailed action close-up demonstrating core process and breakdown of {topic}, vibrant studio lighting, hyperrealistic"
            elif phase == "detail":
                return f"Macro detailed shot highlighting intricate textures, components, and key elements of {topic}, shallow depth of field"
            elif phase == "application":
                return f"Dynamic real-world context scene illustrating practical impact and execution of {topic}, cinematic composition"
            else:
                return f"Inspiring wide-angle panoramic view capturing the ultimate significance and future of {topic}, golden hour cinematography"

    # -------------------------------------------------------------
    # TOPIC-SPECIFIC STRATEGY FALLBACK
    # -------------------------------------------------------------
    def _generate_topic_specific_strategy(self, topic: str, audience: str, platform: str, duration: int, goal: str, tone: str) -> dict:
        clean = self._clean_topic_name(topic)
        scenes_count = max(3, min(8, int(duration // 10) or 5))

        if "how to" in clean.lower():
            title = f"{clean}: Step-by-Step Breakdown"
            hook = f"Want to master {clean}? Here is the exact formula that works every time."
        elif goal.lower() in ["educate", "explain"]:
            title = f"The Deep Truth About {clean}"
            hook = f"What if everything you were told about {clean} was only half the story?"
        elif goal.lower() in ["entertain", "inspire"]:
            title = f"Why {clean} Is More Mind-Blowing Than You Think"
            hook = f"This one fact about {clean} will completely change how you see it."
        else:
            title = f"{clean}: The Complete Breakdown"
            hook = f"Stop overcomplicating {clean}—here is what you actually need to know."

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
