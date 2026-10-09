import os
import io
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

    def _get_dimensions(self, aspect_ratio: str):
        if aspect_ratio == "9:16":
            return 1080, 1920
        elif aspect_ratio == "1:1":
            return 1080, 1080
        elif aspect_ratio == "4:5":
            return 1080, 1350
        else: # 16:9
            return 1920, 1080

    def _extract_keywords(self, description: str) -> str:
        """Extracts the most relevant search keywords from the scene visual description."""
        stopwords = {
            "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with",
            "from", "by", "is", "are", "was", "were", "showing", "looking", "pointing",
            "studying", "modern", "friendly", "of", "where", "that", "this"
        }
        words = re.findall(r'[a-zA-Z]+', description.lower())
        meaningful = [w for w in words if w not in stopwords and len(w) > 2]
        return " ".join(meaningful[:3]) if meaningful else "cinematic landscape"

    def _try_pollinations_ai(self, description: str, width: int, height: int, seed: int = 1) -> Image.Image:
        """Attempts to generate a real AI image via Pollinations with a unique seed per scene."""
        clean_prompt = f"{description}, cinematic lighting, photorealistic, 8k, highly detailed"
        encoded = urllib.parse.quote(clean_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&seed={seed}&nologo=true"
        
        headers = {}
        if self.pollinations_api_key:
            headers["Authorization"] = f"Bearer {self.pollinations_api_key}"

        res = requests.get(url, headers=headers, timeout=20)
        res.raise_for_status()
        
        img = Image.open(io.BytesIO(res.content)).convert("RGB")
        w, h = img.size
        if h > 100:
            img = img.crop((0, 0, w, h - 75))
        return ImageOps.fit(img, (width, height), Image.Resampling.LANCZOS)

    def _try_wikimedia_search(self, description: str, width: int, height: int, scene_index: int = 1) -> Image.Image:
        """Searches high-quality real photographs matching the scene description from Wikimedia Commons, ensuring distinct image per scene."""
        query = self._extract_keywords(description)
        url = "https://commons.wikimedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": 12,
            "prop": "imageinfo",
            "iiprop": "url|mime",
            "iiurlwidth": max(width, 1280)
        }
        headers = {"User-Agent": "QoneqtContentStudio/1.0 (contact@qoneqt.com)"}
        
        r = requests.get(url, params=params, headers=headers, timeout=12)
        pages = r.json().get("query", {}).get("pages", {})
        
        valid_urls = []
        for p in pages.values():
            infos = p.get("imageinfo", [])
            if not infos:
                continue
            mime = infos[0].get("mime", "")
            if mime in ["image/jpeg", "image/png", "image/webp"]:
                u = infos[0].get("thumburl") or infos[0].get("url")
                if u and u not in valid_urls:
                    valid_urls.append(u)
                    
        if not valid_urls:
            raise Exception(f"No valid images found for query '{query}'")
            
        # Pick distinct image for this specific scene index
        chosen_idx = (scene_index - 1) % len(valid_urls)
        img_url = valid_urls[chosen_idx]
        img_res = requests.get(img_url, headers=headers, timeout=15)
        if img_res.status_code == 200:
            img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
            return ImageOps.fit(img, (width, height), Image.Resampling.LANCZOS)
            
        raise Exception("Failed to download selected wikimedia image")

    def _try_picsum_photography(self, width: int, height: int, seed: int = 1) -> Image.Image:
        """Fetches high-resolution dynamic real photography guaranteed to differ per scene via seed."""
        url = f"https://picsum.photos/seed/{seed}/{width}/{height}"
        res = requests.get(url, timeout=12)
        res.raise_for_status()
        img = Image.open(io.BytesIO(res.content)).convert("RGB")
        return ImageOps.fit(img, (width, height), Image.Resampling.LANCZOS)

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
        scene_index: int = 1
    ) -> str:
        width, height = self._get_dimensions(aspect_ratio)
        img = None
        
        # Backward compatibility for text parameter
        if text and not title:
            title = text

        # Calculate a deterministic yet unique seed for this specific scene
        seed = (scene_index * 1337) + (abs(hash(description or title or caption)) % 100000)

        # Tier 1: Pollinations AI with scene seed
        try:
            img = self._try_pollinations_ai(description, width, height, seed=seed)
        except Exception:
            pass

        # Tier 2: Real matching photography from Wikimedia Commons (distinct image per scene_index)
        if img is None:
            try:
                img = self._try_wikimedia_search(description, width, height, scene_index=scene_index)
            except Exception:
                pass

        # Tier 3: Real dynamic high-resolution photography with unique seed
        if img is None:
            try:
                img = self._try_picsum_photography(width, height, seed=seed)
            except Exception:
                pass

        # Tier 4: Modern Dark Gradient fallback with distinct hue per scene
        if img is None:
            hue_offset = (scene_index * 35) % 255
            img = Image.new("RGB", (width, height), color=(15 + (hue_offset // 10), 23 + (hue_offset // 8), 42 + (hue_offset // 6)))

        # 1. Overlay Title Shifted to the TOP of the frame
        if title:
            img = self._overlay_top_title(img, title, width, height, aspect_ratio)

        # 2. Overlay Speech Caption in the lower-third
        if caption:
            img = self._overlay_speech_caption(img, caption, width, height, aspect_ratio)

        filename = f"{uuid.uuid4().hex}.jpg"
        filepath = os.path.join(self.output_dir, filename)
        img.save(filepath, "JPEG", quality=95)
        return filepath

image_service = ImageService()
