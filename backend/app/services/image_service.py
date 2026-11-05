import os
import io
import time
import uuid
import re
import urllib.parse
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
from app.config import settings

class ImageService:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.output_dir = os.path.join(base_dir, "storage", "assets", "images")
        os.makedirs(self.output_dir, exist_ok=True)
        self.pollinations_api_key = getattr(settings, "POLLINATIONS_API_KEY", "") or os.getenv("POLLINATIONS_API_KEY", "")
        self.pollinations_cooldown = 0

    def _get_dimensions(self, aspect_ratio: str):
        if aspect_ratio == "9:16":
            return 1080, 1920
        elif aspect_ratio == "1:1":
            return 1080, 1080
        elif aspect_ratio == "4:5":
            return 1080, 1350
        else: # 16:9
            return 1920, 1080

    def _extract_topic_anchor(self, topic: str) -> str:
        """Extracts the primary concrete subject keyword or short noun phrase representing the topic."""
        if not topic:
            return ""
        clean = re.sub(r'^(how\s+to\s+(?:make|build|cook|change|play|fix|do|learn|master|create|use)?|guide\s+to\s+|tips\s+for\s+|ways\s+to\s+|secrets?\s+of\s+|\d+\s*)', '', topic.strip(), flags=re.IGNORECASE).strip()
        words = [w for w in re.findall(r'[a-zA-Z]+', clean.lower()) if len(w) > 2 and w not in ["the", "and", "for", "with", "about", "how", "why", "what", "making", "breakdown", "complete", "deep", "truth"]]
        if not words:
            all_words = [w for w in re.findall(r'[a-zA-Z]+', topic.lower()) if len(w) > 2]
            return all_words[0] if all_words else ""
        
        joined = " ".join(words)
        if "pizza" in joined:
            return "pizza"
        if "burger" in joined or "patty" in joined:
            return "burger"
        if "coffee" in joined or "espresso" in joined:
            return "espresso" if "espresso" in joined else "coffee"
        if "sourdough" in joined or "bread" in joined:
            return "sourdough bread"
        if "pasta" in joined or "noodle" in joined:
            return "pasta"
        if "tire" in joined or "car" in joined or "automotive" in joined or "wheel" in joined:
            return "car tire"
        if "guitar" in joined:
            return "acoustic guitar"
        if "dog" in joined or "puppy" in joined or "pet" in joined:
            return "dog"
        if "cyber" in joined or "security" in joined:
            return "cybersecurity"
        if "habit" in joined or "morning" in joined or "routine" in joined:
            return "morning routine"
        if "back" in joined and "pain" in joined:
            return "back pain"
        if "coding" in joined or "python" in joined or "program" in joined:
            return "coding"
        if "space" in joined or "galaxy" in joined or "astronomy" in joined:
            return "space"
        if "garden" in joined or "plant" in joined:
            return "gardening"
        if "meditat" in joined:
            return "meditation"
        if "yoga" in joined:
            return "yoga"
        if "finance" in joined or "money" in joined or "stock" in joined or "invest" in joined:
            return "finance"
            
        return words[0]

    def _derive_search_queries(self, title: str = "", narration: str = "", description: str = "", topic: str = "") -> list[str]:
        """Extracts prioritized, strictly topic-anchored photography search queries matching the scene subject."""
        queries = []
        topic_anchor = self._extract_topic_anchor(topic)
        combined_text = f"{title} {narration} {description}".lower()

        filler = {
            "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with",
            "from", "by", "is", "are", "was", "were", "showing", "looking", "pointing",
            "studying", "modern", "friendly", "of", "where", "that", "this", "cinematic",
            "photorealistic", "detailed", "clean", "minimalist", "shot", "ultra",
            "hyperrealistic", "close", "macro", "establishing", "lighting", "soft",
            "ambient", "resolution", "res", "focus", "atmosphere", "ambience", "view",
            "wide", "angle", "high", "end", "beautiful", "dramatic", "habit", "step",
            "scene", "tip", "rule", "taking", "demonstrating", "overlooking", "feeling",
            "accomplishment", "environment", "person", "motivated", "aspirational",
            "professional", "setup", "great", "best", "simple", "easy", "part",
            "secret", "core", "foundation", "understanding", "mastering", "breakdown"
        }

        # Domain/topic specific visual concept mapping
        if topic_anchor == "pizza" or "pizza" in combined_text or "pizza" in topic.lower():
            title_lower = title.lower()
            if any(w in title_lower for w in ["dough", "ferment", "flour", "knead", "yeast", "ingredient", "base"]):
                queries.extend(["pizza dough", "kneading pizza dough", "pizza dough ball"])
            elif any(w in title_lower for w in ["sauce", "simplicity", "tomato", "cheese", "mozzarella", "topping", "layer", "flavor"]):
                queries.extend(["pizza sauce", "pizza mozzarella", "pizza tomato sauce"])
            elif any(w in title_lower for w in ["heat", "oven", "blister", "fire", "bake", "temperature"]):
                queries.extend(["pizza wood oven", "pizza oven", "wood fired pizza oven"])
            elif any(w in title_lower for w in ["drizzle", "oil", "finish", "olive", "basil", "seasoning"]):
                queries.extend(["pizza basil", "margherita pizza basil", "pizza olive oil"])
            elif any(w in title_lower for w in ["slice", "perfect", "eat", "serve", "pull", "piece"]):
                queries.extend(["pizza slice", "pizza cheese pull", "margherita pizza slice"])
            elif any(w in combined_text for w in ["dough", "knead", "flour"]):
                queries.extend(["pizza dough", "kneading pizza dough"])
            elif any(w in combined_text for w in ["sauce", "tomato", "mozzarella"]):
                queries.extend(["pizza sauce", "pizza mozzarella"])
            elif any(w in combined_text for w in ["wood-fired", "brick oven", "oven"]):
                queries.extend(["pizza wood oven", "pizza oven"])
            elif any(w in combined_text for w in ["cheese pull", "perfect slice"]):
                queries.extend(["pizza slice", "pizza cheese pull"])
            else:
                queries.extend(["margherita pizza", "pizza oven", "pizza dough", "pizza slice"])

        elif topic_anchor == "car tire" or "tire" in topic.lower() or "car" in topic.lower():
            if any(w in combined_text for w in ["lug", "wrench", "loosen", "nut"]):
                queries.extend(["car wheel lug wrench", "car tire lug nuts", "changing car wheel"])
            elif any(w in combined_text for w in ["jack", "lift", "raise", "hydraulic"]):
                queries.extend(["hydraulic car jack", "car jack wheel", "car lift jack"])
            elif any(w in combined_text for w in ["swap", "spare", "mount", "stud"]):
                queries.extend(["car spare tire", "car spare wheel", "mounting car tire"])
            elif any(w in combined_text for w in ["torque", "tighten", "star"]):
                queries.extend(["torque wrench car wheel", "tightening car tire", "car wheel lug nuts"])
            else:
                queries.extend(["car tire maintenance", "car wheel tire", "changing car tire"])

        elif topic_anchor == "acoustic guitar" or "guitar" in topic.lower():
            if any(w in combined_text for w in ["fret", "thumb", "neck", "grip"]):
                queries.extend(["acoustic guitar fretboard", "guitar neck fingers", "acoustic guitar chords"])
            elif any(w in combined_text for w in ["strum", "pick", "rhythm", "wrist"]):
                queries.extend(["strumming acoustic guitar", "acoustic guitar soundhole", "guitar plectrum strumming"])
            elif any(w in combined_text for w in ["shift", "chord", "transition"]):
                queries.extend(["acoustic guitar chords", "guitar chord transition", "acoustic guitar fingers"])
            else:
                queries.extend(["acoustic guitar playing", "acoustic guitar music", "acoustic guitar"])

        elif topic_anchor == "burger" or "burger" in topic.lower():
            if any(w in combined_text for w in ["smash", "sear", "skillet", "beef", "patty"]):
                queries.extend(["smash burger skillet", "sizzling beef burger patty", "burger patty grill"])
            elif any(w in combined_text for w in ["cheese", "cheddar", "melt", "dome"]):
                queries.extend(["cheeseburger melted cheddar", "melted cheese burger", "cheeseburger"])
            elif any(w in combined_text for w in ["bun", "brioche", "toast"]):
                queries.extend(["toasted brioche burger bun", "brioche bun burger", "cheeseburger brioche"])
            else:
                queries.extend(["gourmet cheeseburger", "smash burger", "cheeseburger"])

        elif topic_anchor in ["coffee", "espresso"] or "coffee" in topic.lower() or "espresso" in topic.lower():
            if any(w in combined_text for w in ["grind", "wdt", "tamp", "basket"]):
                queries.extend(["espresso portafilter", "barista espresso grounds", "tamping espresso"])
            elif any(w in combined_text for w in ["extract", "crema", "pressure", "stream"]):
                queries.extend(["espresso extraction crema", "espresso machine pull", "artisan espresso crema"])
            elif any(w in combined_text for w in ["steam", "milk", "microfoam", "latte", "art"]):
                queries.extend(["barista latte art", "pouring latte art", "espresso latte art"])
            else:
                queries.extend(["artisan espresso", "espresso cup crema", "coffee espresso"])

        elif topic_anchor == "morning routine" or "morning" in topic.lower() or "habit" in topic.lower():
            if any(w in combined_text for w in ["sunlight", "sun", "sunrise"]):
                queries.extend(["morning sunlight", "morning sun", "sunrise morning"])
            elif any(w in combined_text for w in ["priority", "planner", "planning"]):
                queries.extend(["notebook planner pen", "daily planner desk", "time management planner"])
            elif any(w in combined_text for w in ["deep work", "focus", "laptop", "desk"]):
                queries.extend(["laptop desk workspace", "laptop computer desk", "computer workstation"])
            elif any(w in combined_text for w in ["movement", "walk", "exercise"]):
                queries.extend(["morning walk park", "walking outdoors park", "morning exercise walk"])
            elif any(w in combined_text for w in ["reflection", "evening", "sunset"]):
                queries.extend(["sunset city evening", "evening skyline sunset", "city sunset"])

        # Title words anchored with topic_anchor
        clean_title = re.sub(r'^(habit|step|scene|tip|rule|secret|part)\s*\d+[:\-]?\s*', '', title, flags=re.IGNORECASE).strip()
        title_words = [w for w in re.findall(r'[a-zA-Z]+', clean_title.lower()) if w not in filler and len(w) > 2]
        if title_words:
            title_phrase = " ".join(title_words[:2])
            if topic_anchor:
                if topic_anchor.lower() not in title_phrase:
                    queries.append(f"{topic_anchor} {title_phrase}")
                else:
                    queries.append(title_phrase)
            else:
                queries.append(title_phrase)

        # Concrete nouns from description anchored with topic_anchor
        abstract_words = {
            "concept", "approach", "method", "overview", "mechanism", "detail", "setting",
            "stage", "components", "elements", "resolution", "textures", "intricate",
            "dynamic", "practical", "execution", "impact", "significance", "future",
            "cinematic", "photorealistic", "lighting", "shallow", "depth", "field"
        }
        desc_words = [w for w in re.findall(r'[a-zA-Z]+', description.lower()) if w not in filler and w not in abstract_words and len(w) > 2]
        if desc_words:
            desc_phrase = " ".join(desc_words[:2])
            if topic_anchor:
                if topic_anchor.lower() not in desc_phrase:
                    queries.append(f"{topic_anchor} {desc_phrase}")
                else:
                    queries.append(desc_phrase)
            else:
                queries.append(desc_phrase)

        # Topic fallback queries (strictly anchored)
        if topic_anchor:
            queries.append(f"{topic_anchor}")
            queries.append(f"{topic_anchor} photography")
        else:
            clean_topic = re.sub(r'^\d+\s*', '', topic).strip()
            topic_words = [w for w in re.findall(r'[a-zA-Z]+', clean_topic.lower()) if w not in filler and len(w) > 2]
            if topic_words:
                queries.append(" ".join(topic_words[:3]))

        # Deduplicate while preserving priority order
        seen = set()
        deduped = []
        for q in queries:
            q_clean = q.strip()
            if q_clean and q_clean.lower() not in seen:
                seen.add(q_clean.lower())
                deduped.append(q_clean)

        return deduped if deduped else [f"{topic_anchor} photography" if topic_anchor else "cinematic photography"]

    def _try_pollinations_ai(self, prompt: str, width: int, height: int, seed: int = 1) -> Image.Image:
        """Attempts to generate a real AI image via Pollinations with a unique seed per scene."""
        clean_prompt = f"{prompt}, authentic photography, natural lighting, photorealistic, 8k, highly detailed"
        encoded = urllib.parse.quote(clean_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&seed={seed}&nologo=true"
        
        headers = {}
        if self.pollinations_api_key:
            headers["Authorization"] = f"Bearer {self.pollinations_api_key}"

        # Fast 18-second timeout so render does not stall if free tier IP rate limit is hit
        res = requests.get(url, headers=headers, timeout=18)
        res.raise_for_status()
        
        img = Image.open(io.BytesIO(res.content)).convert("RGB")
        w, h = img.size
        if h > 100:
            img = img.crop((0, 0, w, h - 75))
        return ImageOps.fit(img, (width, height), Image.Resampling.LANCZOS)

    def _try_wikimedia_search(self, queries: list[str], width: int, height: int, scene_index: int = 1, topic_anchor: str = "") -> Image.Image:
        """Searches high-quality real photographs strictly matching the scene queries from Wikimedia Commons."""
        headers = {"User-Agent": "QoneqtContentStudio/1.0 (contact@qoneqt.com)"}
        
        # Base negative keywords (always exclude non-photographic and cemetery content)
        active_negative = {
            "stamp", "postage", "tombstone", "cemetery", "grave",
            "map", "diagram", "chart", "graph", "infographic", "drawing", "sketch", "icon", "logo", "flag"
        }
        
        # Context-aware exclusions so we don't block legitimate topic photography
        anchor_tokens = [t for t in re.findall(r'[a-zA-Z]+', (topic_anchor or "").lower()) if len(t) > 2]
        is_auto = any(t in ["car", "tire", "auto", "vehicle", "wheel", "mechanic"] for t in anchor_tokens)
        is_music = any(t in ["music", "guitar", "concert", "band", "sound"] for t in anchor_tokens)
        is_finance = any(t in ["money", "finance", "coin", "currency", "bank", "wealth"] for t in anchor_tokens)
        
        if not is_auto:
            active_negative.update({"bus", "truck", "automobile", "cadillac", "vehicle", "van", "train", "locomotive", "railway", "aircraft", "airplane", "aviation"})
        if not is_music:
            active_negative.update({"concert", "crowd", "stage", "musician", "band"})
        if not is_finance:
            active_negative.update({"coin", "currency", "banknote"})
        
        for q in queries:
            try:
                url = "https://commons.wikimedia.org/w/api.php"
                params = {
                    "action": "query",
                    "format": "json",
                    "generator": "search",
                    "gsrsearch": f"filetype:bitmap {q}",
                    "gsrnamespace": 6,
                    "gsrlimit": 10,
                    "prop": "imageinfo",
                    "iiprop": "url|mime",
                    "iiurlwidth": max(width, 1280)
                }
                
                r = requests.get(url, params=params, headers=headers, timeout=8)
                pages = r.json().get("query", {}).get("pages", {})
                
                valid_urls = []
                for p in pages.values():
                    p_title = p.get("title", "").lower()
                    if any(neg in p_title for neg in active_negative):
                        continue
                    infos = p.get("imageinfo", [])
                    if not infos:
                        continue
                    mime = infos[0].get("mime", "")
                    if mime in ["image/jpeg", "image/png", "image/webp"]:
                        u = infos[0].get("thumburl") or infos[0].get("url")
                        if u and not u.endswith(".pdf") and not u.endswith(".svg"):
                            # Strictly require anchor tokens if topic_anchor is present
                            if anchor_tokens:
                                if any(tok in p_title for tok in anchor_tokens):
                                    valid_urls.append(u)
                            else:
                                valid_urls.append(u)
                            
                if not valid_urls:
                    continue
                    
                # Pick distinct image for this specific scene index
                start_idx = (scene_index - 1) % len(valid_urls)
                for offset in range(len(valid_urls)):
                    img_url = valid_urls[(start_idx + offset) % len(valid_urls)]
                    try:
                        img_res = requests.get(img_url, headers=headers, timeout=8)
                        if img_res.status_code == 200 and len(img_res.content) > 5000:
                            img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
                            print(f"[ImageService] Found topic-matched photo for scene {scene_index} (query: '{q}'): {img_url[:70]}...")
                            return ImageOps.fit(img, (width, height), Image.Resampling.LANCZOS)
                    except Exception:
                        continue
            except Exception:
                continue
                
        # Fallback to guaranteed topic anchor photography query
        if topic_anchor and anchor_tokens:
            try:
                url = "https://commons.wikimedia.org/w/api.php"
                params = {
                    "action": "query",
                    "format": "json",
                    "generator": "search",
                    "gsrsearch": f"filetype:bitmap {topic_anchor} photography",
                    "gsrnamespace": 6,
                    "gsrlimit": 10,
                    "prop": "imageinfo",
                    "iiprop": "url|mime",
                    "iiurlwidth": max(width, 1280)
                }
                r = requests.get(url, params=params, headers=headers, timeout=8)
                pages = r.json().get("query", {}).get("pages", {})
                valid_urls = []
                for p in pages.values():
                    p_title = p.get("title", "").lower()
                    if any(neg in p_title for neg in active_negative):
                        continue
                    infos = p.get("imageinfo", [])
                    if not infos:
                        continue
                    mime = infos[0].get("mime", "")
                    if mime in ["image/jpeg", "image/png", "image/webp"]:
                        u = infos[0].get("thumburl") or infos[0].get("url")
                        if u and any(tok in p_title for tok in anchor_tokens):
                            valid_urls.append(u)
                if valid_urls:
                    start_idx = (scene_index - 1) % len(valid_urls)
                    img_url = valid_urls[start_idx]
                    img_res = requests.get(img_url, headers=headers, timeout=8)
                    if img_res.status_code == 200 and len(img_res.content) > 5000:
                        img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
                        print(f"[ImageService] Found guaranteed topic-anchor photo for scene {scene_index}: {img_url[:70]}...")
                        return ImageOps.fit(img, (width, height), Image.Resampling.LANCZOS)
            except Exception as e:
                print(f"[ImageService] Anchor fallback note: {e}")

        raise Exception(f"No valid topic-anchored images found on Wikimedia Commons for '{topic_anchor}'")

    def _create_themed_fallback(self, width: int, height: int, scene_index: int = 1) -> Image.Image:
        """Creates a modern, elegant gradient studio card with subtle lighting accents."""
        hue_offset = (scene_index * 45) % 255
        r = 15 + ((hue_offset * 2) % 30)
        g = 22 + ((hue_offset * 3) % 40)
        b = 38 + ((hue_offset * 4) % 55)
        
        img = Image.new("RGB", (width, height), color=(r, g, b))
        draw = ImageDraw.Draw(img)
        # Subtle modern border glow
        accent_color = (min(255, r + 50), min(255, g + 80), min(255, b + 120))
        draw.rectangle([16, 16, width - 16, height - 16], outline=accent_color, width=2)
        return img

    def _get_font(self, font_size: int):
        """Loads a clean, high-legibility bold TrueType font with fallbacks."""
        windir = os.environ.get("WINDIR", "C:\\Windows")
        fonts_dir = os.path.join(windir, "Fonts")
        candidate_fonts = ["segoeuib.ttf", "arialbd.ttf", "calibrib.ttf", "segoeui.ttf", "arial.ttf"]

        for font_name in candidate_fonts:
            try:
                full_path = os.path.join(fonts_dir, font_name)
                if os.path.exists(full_path):
                    return ImageFont.truetype(full_path, font_size)
                else:
                    return ImageFont.truetype(font_name, font_size)
            except Exception:
                continue

        return ImageFont.load_default()

    def _overlay_top_title(self, img: Image.Image, title: str, width: int, height: int, aspect_ratio: str = "9:16") -> Image.Image:
        """Overlays a prominent, modern title badge shifted cleanly to the TOP of the video frame."""
        if not title or not title.strip():
            return img

        clean_title = title.strip()
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        font_size = max(28, int(width * 0.038))
        font = self._get_font(font_size)

        # Word wrap title if long
        words = clean_title.split()
        lines = []
        current_line = []
        max_line_width = int(width * 0.84)

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if (bbox[2] - bbox[0]) <= max_line_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        if current_line:
            lines.append(" ".join(current_line))

        # Restrict title to at most 2 lines
        lines = lines[:2]

        line_widths = []
        line_heights = []
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_widths.append(bbox[2] - bbox[0])
            line_heights.append(bbox[3] - bbox[1])

        total_text_height = sum(line_heights) + (len(lines) - 1) * 10
        max_w = max(line_widths) if line_widths else 100

        pad_x = 36
        pad_y = 16
        box_w = max_w + (pad_x * 2)
        box_h = total_text_height + (pad_y * 2)

        box_x = (width - box_w) / 2
        # SHIFT TITLE TO TOP (approx 7-8% from top for vertical, 5% for horizontal)
        box_y = int(height * 0.06) if aspect_ratio == "16:9" else int(height * 0.08)

        # Sleek dark glass capsule with electric blue accent border
        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h],
            radius=20,
            fill=(15, 23, 42, 230),
            outline=(59, 130, 246, 220), # Vibrant electric blue highlight
            width=3
        )

        curr_y = box_y + pad_y
        for i, line in enumerate(lines):
            line_w = line_widths[i]
            text_x = box_x + (box_w - line_w) / 2
            draw.text((text_x, curr_y), line, fill=(255, 255, 255, 255), font=font)
            curr_y += line_heights[i] + 10

        return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    def _overlay_speech_caption(self, img: Image.Image, caption: str, width: int, height: int, aspect_ratio: str = "9:16") -> Image.Image:
        """Overlays the speech narration caption cleanly in the lower-third with optimal legibility."""
        if not caption or not caption.strip():
            return img

        clean_caption = caption.strip()
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Dynamically scale font size based on caption length so speech is always fully readable
        word_count = len(clean_caption.split())
        if word_count > 30:
            font_size = max(24, int(width * 0.030))
        elif word_count > 16:
            font_size = max(28, int(width * 0.035))
        else:
            font_size = max(32, int(width * 0.040))

        font = self._get_font(font_size)

        # Word wrap text
        words = clean_caption.split()
        lines = []
        current_line = []
        max_line_width = int(width * 0.82)

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if (bbox[2] - bbox[0]) <= max_line_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        if current_line:
            lines.append(" ".join(current_line))

        # Keep caption within 4 lines max for clean visual presentation
        if len(lines) > 4:
            lines = lines[:4]

        line_widths = []
        line_heights = []
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_widths.append(bbox[2] - bbox[0])
            line_heights.append(bbox[3] - bbox[1])

        total_text_height = sum(line_heights) + (len(lines) - 1) * 10
        max_w = max(line_widths) if line_widths else 100

        pad_x = 34
        pad_y = 18
        box_w = max_w + (pad_x * 2)
        box_h = total_text_height + (pad_y * 2)

        box_x = (width - box_w) / 2
        # Position caption in the lower third
        box_y = int(height * 0.76) if aspect_ratio == "16:9" else int(height * 0.72)

        # High-retention subtitle capsule with soft glow
        draw.rounded_rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h],
            radius=22,
            fill=(10, 15, 28, 235),
            outline=(255, 255, 255, 80),
            width=2
        )

        curr_y = box_y + pad_y
        for i, line in enumerate(lines):
            line_w = line_widths[i]
            text_x = box_x + (box_w - line_w) / 2
            draw.text((text_x, curr_y), line, fill=(255, 255, 255, 255), font=font)
            curr_y += line_heights[i] + 10

        return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    def generate_scene_visual(
        self, 
        description: str, 
        title: str = "", 
        caption: str = "", 
        text: str = "", 
        aspect_ratio: str = "9:16", 
        scene_index: int = 1,
        topic: str = ""
    ) -> str:
        width, height = self._get_dimensions(aspect_ratio)
        img = None
        
        # Backward compatibility for text parameter
        if text and not title:
            title = text

        # Extract topic anchor for filtering and prioritization
        topic_anchor = self._extract_topic_anchor(topic)

        # Derive high-relevance search queries matching scene and topic
        queries = self._derive_search_queries(
            title=title,
            narration=caption,
            description=description,
            topic=topic
        )

        # Calculate a deterministic yet unique seed for this specific scene
        seed = (scene_index * 1337) + (abs(hash(description or title or caption or topic)) % 100000)

        # Tier 1: Pollinations AI with prompt strictly adhering to scene subject
        ai_prompt = f"{topic}: {title}, {description or caption}"
        if time.time() >= self.pollinations_cooldown:
            try:
                print(f"[ImageService] Attempting Pollinations AI generation for scene {scene_index}...")
                img = self._try_pollinations_ai(ai_prompt, width, height, seed=seed)
                print(f"[ImageService] Pollinations AI succeeded for scene {scene_index}")
            except Exception as ai_err:
                if any(err_code in str(ai_err) for err_code in ["402", "429"]):
                    self.pollinations_cooldown = time.time() + 45
                print(f"[ImageService] Pollinations AI unavailable ({ai_err}). Switching to topic-matched photography...")
        else:
            print(f"[ImageService] Pollinations cooldown active (free tier rate limit), using topic-matched photography...")

        # Tier 2: Real topic-matched high-quality photography from Wikimedia Commons
        if img is None:
            try:
                img = self._try_wikimedia_search(queries, width, height, scene_index=scene_index, topic_anchor=topic_anchor)
            except Exception as wiki_err:
                print(f"[ImageService] Wikimedia search warning: {wiki_err}")

        # Tier 3: Modern elegant gradient studio card (strictly topic-neutral, no random picsum photos)
        if img is None:
            print(f"[ImageService] Using aesthetic gradient studio card fallback for scene {scene_index}")
            img = self._create_themed_fallback(width, height, scene_index=scene_index)

        # 1. Overlay Title Shifted cleanly to the TOP of the frame
        if title:
            img = self._overlay_top_title(img, title, width, height, aspect_ratio)

        # 2. Overlay Speech Caption in the lower-third with optimal legibility
        if caption:
            img = self._overlay_speech_caption(img, caption, width, height, aspect_ratio)

        filename = f"{uuid.uuid4().hex}.jpg"
        filepath = os.path.join(self.output_dir, filename)
        img.save(filepath, "JPEG", quality=95)
        return filepath

image_service = ImageService()
