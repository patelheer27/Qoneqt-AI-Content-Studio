import os
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def get_font(size: int, bold: bool = False):
    """Safely loads a clean system font or falls back to PIL default font"""
    font_candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in font_candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()

def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """Wraps text so it fits within max_width pixels"""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
                current_line = []
    if current_line:
        lines.append(" ".join(current_line))
    return lines or [text]

def generate_scene_image(
    scene_number: int,
    total_scenes: int,
    topic: str,
    on_screen_text: str,
    visual_prompt: str,
    output_path: Path,
    width: int = 1080,
    height: int = 1920
) -> Path:
    """
    Generates a vertical 1080x1920 graphic card with a modern SaaS aesthetic.
    """
    # Color Palettes per scene
    palettes = [
        # Scene 1: Electric Indigo / Purple
        {"bg_top": (10, 15, 30), "bg_bot": (35, 12, 55), "accent": (147, 51, 234), "highlight": (192, 132, 252)},
        # Scene 2: Emerald Cyber
        {"bg_top": (8, 22, 28), "bg_bot": (5, 50, 40), "accent": (16, 185, 129), "highlight": (110, 231, 183)},
        # Scene 3: Electric Cyan / Blue
        {"bg_top": (5, 15, 35), "bg_bot": (10, 45, 75), "accent": (6, 182, 212), "highlight": (103, 232, 249)},
        # Scene 4: Amber / Ruby Neon
        {"bg_top": (25, 10, 20), "bg_bot": (65, 15, 30), "accent": (244, 63, 94), "highlight": (251, 146, 60)},
        # Scene 5: Modern Violet Violet
        {"bg_top": (12, 10, 26), "bg_bot": (45, 10, 70), "accent": (168, 85, 247), "highlight": (232, 121, 249)},
    ]
    palette = palettes[(scene_number - 1) % len(palettes)]

    # Create canvas
    img = Image.new("RGB", (width, height), palette["bg_top"])
    draw = ImageDraw.Draw(img)

    # 1. Vertical Gradient background
    for y in range(height):
        factor = y / height
        r = int(palette["bg_top"][0] * (1 - factor) + palette["bg_bot"][0] * factor)
        g = int(palette["bg_top"][1] * (1 - factor) + palette["bg_bot"][1] * factor)
        b = int(palette["bg_top"][2] * (1 - factor) + palette["bg_bot"][2] * factor)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # 2. Ambient glowing circles (light flares)
    glow_center_x = width // 2
    glow_center_y = int(height * 0.42)
    glow_radius = 420
    for r_offset in range(glow_radius, 0, -18):
        alpha_factor = (1 - (r_offset / glow_radius)) ** 2
        glow_r = int(palette["accent"][0] * alpha_factor * 0.45)
        glow_g = int(palette["accent"][1] * alpha_factor * 0.45)
        glow_b = int(palette["accent"][2] * alpha_factor * 0.45)
        draw.ellipse(
            [
                (glow_center_x - r_offset, glow_center_y - r_offset),
                (glow_center_x + r_offset, glow_center_y + r_offset)
            ],
            outline=None,
            fill=(glow_r, glow_g, glow_b)
        )

    # 3. Header Branding Bar
    # Pill background for "QONEQT AI CONTENT STUDIO"
    draw.rounded_rectangle([(100, 160), (width - 100, 250)], radius=45, fill=(15, 23, 42), outline=(51, 65, 85), width=2)
    # Glowing dot
    draw.ellipse([(140, 195), (160, 215)], fill=palette["highlight"])
    header_font = get_font(34, bold=True)
    draw.text((180, 185), "QONEQT  •  AI CONTENT STUDIO", font=header_font, fill=(241, 245, 249))

    # 4. Scene Progress Indicator Badge
    scene_badge_text = f"SCENE 0{scene_number} / 0{total_scenes}" if total_scenes < 10 else f"SCENE {scene_number} / {total_scenes}"
    badge_font = get_font(28, bold=True)
    draw.rounded_rectangle([(100, 310), (440, 380)], radius=20, fill=palette["accent"])
    draw.text((130, 328), scene_badge_text, font=badge_font, fill=(255, 255, 255))

    # Topic badge on the right
    topic_short = topic if len(topic) <= 24 else topic[:22] + "..."
    small_font = get_font(24, bold=False)
    draw.rounded_rectangle([(460, 310), (width - 100, 380)], radius=20, fill=(30, 41, 59), outline=(71, 85, 105), width=2)
    draw.text((490, 330), topic_short, font=small_font, fill=(203, 213, 225))

    # 5. Main Content Card (Center Stage)
    card_top = 440
    card_bottom = 1420
    draw.rounded_rectangle([(80, card_top), (width - 80, card_bottom)], radius=36, fill=(15, 23, 42), outline=palette["accent"], width=3)

    # Decorative inner glowing accent bar
    draw.line([(140, card_top + 40), (width - 140, card_top + 40)], fill=palette["highlight"], width=4)

    # 6. On-Screen Headline / Focus Text
    headline_font = get_font(56, bold=True)
    headline_lines = wrap_text(on_screen_text, headline_font, width - 260, draw)

    text_y = card_top + 100
    for line in headline_lines[:4]:  # max 4 prominent lines
        bbox = draw.textbbox((0, 0), line, font=headline_font)
        text_w = bbox[2] - bbox[0]
        text_x = (width - text_w) // 2
        # Subtle text drop shadow
        draw.text((text_x + 3, text_y + 3), line, font=headline_font, fill=(0, 0, 0))
        draw.text((text_x, text_y), line, font=headline_font, fill=(255, 255, 255))
        text_y += 82

    # 7. Visual Prompt / Concept Insight Card inside the main card
    concept_box_top = max(text_y + 40, card_top + 460)
    concept_box_bot = card_bottom - 160
    draw.rounded_rectangle([(130, concept_box_top), (width - 130, concept_box_bot)], radius=24, fill=(30, 41, 59), outline=(71, 85, 105), width=2)

    concept_label_font = get_font(26, bold=True)
    draw.text((170, concept_box_top + 30), "VISUAL DIRECTIVE", font=concept_label_font, fill=palette["highlight"])

    concept_font = get_font(30, bold=False)
    clean_prompt = visual_prompt if len(visual_prompt) <= 150 else visual_prompt[:147] + "..."
    prompt_lines = wrap_text(clean_prompt, concept_font, width - 360, draw)
    p_y = concept_box_top + 75
    for pline in prompt_lines[:3]:
        draw.text((170, p_y), pline, font=concept_font, fill=(226, 232, 240))
        p_y += 46

    # 8. Simulated Audio Spectrum / Dynamic waveform at bottom of card
    waveform_y = card_bottom - 90
    bar_width = 12
    bar_gap = 10
    num_bars = 28
    start_x = (width - (num_bars * (bar_width + bar_gap))) // 2
    for i in range(num_bars):
        bar_h = int(20 + 35 * math.sin((i + scene_number * 3) * 0.45) ** 2)
        bx = start_x + i * (bar_width + bar_gap)
        draw.rounded_rectangle([(bx, waveform_y - bar_h), (bx + bar_width, waveform_y)], radius=6, fill=palette["highlight"])

    # 9. Bottom Footer Section
    # Progress bars for video scenes
    prog_y = 1520
    seg_width = int((width - 200 - (total_scenes - 1) * 12) / total_scenes)
    for s_idx in range(total_scenes):
        sx = 100 + s_idx * (seg_width + 12)
        if s_idx < scene_number:
            fill_color = palette["highlight"]
        elif s_idx == scene_number - 1:
            fill_color = palette["accent"]
        else:
            fill_color = (51, 65, 85)
        draw.rounded_rectangle([(sx, prog_y), (sx + seg_width, prog_y + 10)], radius=5, fill=fill_color)

    # Subtitle / Hook indicator
    footer_label_font = get_font(30, bold=True)
    draw.text((100, 1560), "AI SYNTHESIS • 9:16 VERTICAL MP4", font=footer_label_font, fill=(148, 163, 184))

    # Safe margin tag
    sub_font = get_font(24, bold=False)
    draw.text((100, 1610), "Auto-composed for Qoneqt Feed, Reels & Shorts", font=sub_font, fill=(100, 116, 139))

    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), format="PNG", quality=95)
    return output_path
