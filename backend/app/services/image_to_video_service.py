import os
import uuid
import time
import subprocess
import shutil
import re
import json
import requests
from typing import Optional, List, Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from app.services.tts_service import tts_service
from app.services.video_service import video_service

class ImageToVideoService:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.storage_dir = os.path.join(self.base_dir, "storage")
        self.uploads_dir = os.path.join(self.storage_dir, "assets", "uploads")
        self.audio_dir = os.path.join(self.storage_dir, "assets", "audio")
        self.renders_dir = os.path.join(self.storage_dir, "renders")
        self.music_dir = os.path.join(self.storage_dir, "assets", "music")
        
        os.makedirs(self.uploads_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        os.makedirs(self.renders_dir, exist_ok=True)
        os.makedirs(self.music_dir, exist_ok=True)
        
        self._ensure_sample_music_tracks()

    def _ensure_sample_music_tracks(self):
        """Generates melodic ambient background music tracks if they don't already exist."""
        tracks = [
            ("ambient_calm.mp3", 220, "sine=frequency=220:duration=30"),
            ("upbeat_modern.mp3", 330, "sine=frequency=330:duration=30"),
            ("corporate_inspire.mp3", 440, "sine=frequency=440:duration=30"),
            ("cinematic_deep.mp3", 165, "sine=frequency=165:duration=30")
        ]
        for filename, freq, lavfi_src in tracks:
            path = os.path.join(self.music_dir, filename)
            if not os.path.exists(path):
                try:
                    # Create a gentle ambient chord texture with tremolo and lowpass
                    cmd = [
                        "ffmpeg", "-y",
                        "-f", "lavfi", "-i", f"sine=frequency={freq}:duration=45",
                        "-f", "lavfi", "-i", f"sine=frequency={int(freq*1.5)}:duration=45",
                        "-filter_complex", "[0:a][1:a]amix=inputs=2[mix];[mix]lowpass=f=800,tremolo=f=1.5:d=0.5,volume=0.4[a]",
                        "-map", "[a]",
                        "-c:a", "libmp3lame", "-b:a", "128k",
                        path
                    ]
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass

    def get_built_in_music_tracks(self) -> List[Dict[str, str]]:
        """Returns catalogue of built-in ambient background music tracks."""
        return [
            {"id": "ambient_calm", "name": "Chill Ambient Dream", "genre": "Ambient / Chill", "url": "/storage/assets/music/ambient_calm.mp3"},
            {"id": "upbeat_modern", "name": "Upbeat Acoustic Rhythm", "genre": "Upbeat / Acoustic", "url": "/storage/assets/music/upbeat_modern.mp3"},
            {"id": "corporate_inspire", "name": "Inspiring Corporate Flow", "genre": "Corporate / Inspirational", "url": "/storage/assets/music/corporate_inspire.mp3"},
            {"id": "cinematic_deep", "name": "Cinematic Narrative Deep", "genre": "Cinematic / Documentary", "url": "/storage/assets/music/cinematic_deep.mp3"}
        ]

    def get_resolution_dimensions(self, aspect_ratio: str, resolution: str = "1080p") -> Tuple[int, int]:
        """Returns pixel width and height for aspect ratio and resolution."""
        is_720 = resolution.lower() == "720p"
        if aspect_ratio == "16:9":
            return (1280, 720) if is_720 else (1920, 1080)
        elif aspect_ratio == "1:1":
            return (720, 720) if is_720 else (1080, 1080)
        else: # 9:16 vertical
            return (720, 1280) if is_720 else (1080, 1920)

    def save_uploaded_image(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Validates and saves an uploaded image (JPG, JPEG, PNG, WEBP, JFIF)."""
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp", ".jfif"]:
            raise ValueError(f"Unsupported image format '{ext}'. Supported formats: JPG, JPEG, PNG, WEBP, JFIF.")
            
        unique_id = uuid.uuid4().hex[:12]
        base_name = os.path.splitext(re.sub(r'[^a-zA-Z0-9_.-]', '', filename))[0]
        # For JFIF files, convert and save as .jpg for maximum cross-browser and FFmpeg compatibility
        target_ext = ".jpg" if ext == ".jfif" else ext
        safe_filename = f"{unique_id}_{base_name}{target_ext}"
        file_path = os.path.join(self.uploads_dir, safe_filename)
        
        # Save temp file first to inspect and convert safely
        temp_path = os.path.join(self.uploads_dir, f"temp_{unique_id}_{filename}")
        with open(temp_path, "wb") as f:
            f.write(file_content)
            
        try:
            with Image.open(temp_path) as img:
                # Normalize EXIF orientation if needed
                img = ImageOps.exif_transpose(img) or img
                w, h = img.size
                img_format = img.format or "JPEG"
                if ext == ".jfif":
                    # Convert to RGB and save as standard high-quality JPEG
                    rgb_img = img.convert("RGB")
                    rgb_img.save(file_path, "JPEG", quality=95)
                else:
                    shutil.move(temp_path, file_path)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(file_path):
                os.remove(file_path)
            raise ValueError(f"Corrupt or invalid image file: {e}")
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

        file_size = os.path.getsize(file_path)
        url = f"/storage/assets/uploads/{safe_filename}"
        
        return {
            "id": unique_id,
            "filename": safe_filename,
            "original_name": filename,
            "file_path": file_path,
            "url": url,
            "width": w,
            "height": h,
            "file_size": file_size,
            "format": "JPEG" if ext == ".jfif" else img_format
        }

    def save_uploaded_audio(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Validates and saves an uploaded audio file (voiceover or music)."""
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".mp3", ".wav", ".m4a", ".ogg", ".aac", ".flac"]:
            raise ValueError(f"Unsupported audio format '{ext}'. Supported: MP3, WAV, M4A, OGG, AAC.")
            
        unique_id = uuid.uuid4().hex[:12]
        safe_filename = f"{unique_id}_{re.sub(r'[^a-zA-Z0-9_.-]', '', filename)}"
        file_path = os.path.join(self.audio_dir, safe_filename)
        
        with open(file_path, "wb") as f:
            f.write(file_content)
            
        duration = video_service.get_audio_duration(file_path)
        file_size = os.path.getsize(file_path)
        url = f"/storage/assets/audio/{safe_filename}"
        
        return {
            "id": unique_id,
            "filename": safe_filename,
            "original_name": filename,
            "file_path": file_path,
            "url": url,
            "duration": round(duration, 2),
            "file_size": file_size
        }

    def _resolve_local_path(self, url_or_path: str) -> str:
        """Converts web storage URL or relative path into an absolute disk path."""
        if not url_or_path:
            return ""
        if os.path.isabs(url_or_path) and os.path.exists(url_or_path):
            return url_or_path
        clean = url_or_path.replace("\\", "/")
        if clean.startswith("/storage/"):
            rel = clean.replace("/storage/", "")
            return os.path.join(self.storage_dir, rel)
        elif clean.startswith("storage/"):
            rel = clean.replace("storage/", "")
            return os.path.join(self.storage_dir, rel)
        return os.path.join(self.storage_dir, clean.lstrip("/"))

    def _get_font(self, font_name: str, font_size: int):
        """Loads TrueType font with fallbacks."""
        windir = os.environ.get("WINDIR", "C:\\Windows")
        fonts_dir = os.path.join(windir, "Fonts")
        font_map = {
            "Inter": ["segoeuib.ttf", "arialbd.ttf", "calibrib.ttf"],
            "Arial": ["arialbd.ttf", "arial.ttf"],
            "Roboto": ["segoeui.ttf", "arial.ttf"],
            "Impact": ["impact.ttf", "arialbd.ttf"],
            "Georgia": ["georgiab.ttf", "georgia.ttf"]
        }
        candidates = font_map.get(font_name, ["segoeuib.ttf", "arialbd.ttf"]) + ["arial.ttf"]
        for cand in candidates:
            p = os.path.join(fonts_dir, cand)
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, font_size)
                except Exception:
                    continue
        return ImageFont.load_default()

    def _parse_font_size(self, size_val: Any, height: int = 1080) -> int:
        """Parses font size cleanly from numbers or strings and scales appropriately."""
        scale = max(0.65, min(1.8, height / 1080.0))
        if isinstance(size_val, (int, float)):
            return max(18, int(size_val * scale))
        
        s = str(size_val).lower().strip()
        if "small" in s:
            base = 28
        elif "large" in s:
            base = 46
        else: # medium or default
            base = 36
            
        try:
            num = int(re.sub(r'[^0-9]', '', s))
            return max(18, int(num * scale))
        except Exception:
            return max(18, int(base * scale))

    def create_subtitle_overlay_image(
        self,
        headline: str,
        text: str,
        width: int,
        height: int,
        font_name: str = "Inter",
        font_size: Any = 36,
        font_color: str = "#FFFFFF",
        bg_style: str = "translucent",
        position: str = "bottom",
        aspect_ratio: str = "9:16"
    ) -> Optional[str]:
        """Generates a crystal-clear transparent PNG subtitle and headline badge overlay."""
        if not headline and not text:
            return None

        actual_font_size = self._parse_font_size(font_size, height)
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # 1. Headline (Upper Badge)
        if headline and headline.strip():
            h_text = headline.strip()
            h_size = max(22, int(actual_font_size * 0.9))
            h_font = self._get_font(font_name, h_size)
            h_bbox = draw.textbbox((0, 0), h_text, font=h_font)
            h_w = h_bbox[2] - h_bbox[0]
            h_h = h_bbox[3] - h_bbox[1]
            
            pad_x, pad_y = 28, 14
            badge_w = h_w + (pad_x * 2)
            badge_h = h_h + (pad_y * 2)
            badge_x = (width - badge_w) / 2
            badge_y = int(height * 0.08) if aspect_ratio != "16:9" else int(height * 0.06)
            
            # Electric blue accent capsule
            draw.rounded_rectangle(
                [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
                radius=18,
                fill=(15, 23, 42, 235),
                outline=(59, 130, 246, 220),
                width=3
            )
            draw.text((badge_x + pad_x, badge_y + pad_y), h_text, fill=(255, 255, 255, 255), font=h_font)

        # 2. Subtitle (Narration Text)
        if text and text.strip():
            s_text = text.strip()
            s_font = self._get_font(font_name, actual_font_size)
            
            # Word wrap into max 4 lines
            max_w = int(width * 0.86)
            words = s_text.split()
            lines = []
            curr_line = []
            
            for word in words:
                candidate = " ".join(curr_line + [word])
                bbox = draw.textbbox((0, 0), candidate, font=s_font)
                if (bbox[2] - bbox[0]) <= max_w:
                    curr_line.append(word)
                else:
                    if curr_line:
                        lines.append(" ".join(curr_line))
                        curr_line = [word]
                    else:
                        lines.append(word)
            if curr_line:
                lines.append(" ".join(curr_line))
                
            lines = lines[:4]
            line_dims = [draw.textbbox((0, 0), l, font=s_font) for l in lines]
            line_widths = [d[2] - d[0] for d in line_dims]
            line_heights = [d[3] - d[1] for d in line_dims]
            total_text_h = sum(line_heights) + (len(lines) - 1) * 8
            max_line_w = max(line_widths) if line_widths else 200
            
            sub_pad_x, sub_pad_y = 32, 16
            box_w = max_line_w + (sub_pad_x * 2)
            box_h = total_text_h + (sub_pad_y * 2)
            box_x = (width - box_w) / 2
            
            # Determine Y position
            if position == "top":
                box_y = int(height * 0.12)
            elif position == "center":
                box_y = (height - box_h) / 2
            else: # bottom
                box_y = int(height * 0.78) if aspect_ratio == "16:9" else int(height * 0.80)
                
            # Parse color
            text_rgb = (255, 255, 255)
            if font_color.startswith("#"):
                hex_str = font_color.lstrip("#")
                if len(hex_str) == 6:
                    try:
                        text_rgb = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
                    except Exception:
                        text_rgb = (255, 255, 255)
                elif len(hex_str) == 3:
                    try:
                        text_rgb = tuple(int(hex_str[i]*2, 16) for i in range(3))
                    except Exception:
                        text_rgb = (255, 255, 255)
            elif "yellow" in font_color.lower() or "gold" in font_color.lower():
                text_rgb = (250, 204, 21)
            elif "cyan" in font_color.lower():
                text_rgb = (34, 211, 238)
            elif "amber" in font_color.lower():
                text_rgb = (245, 158, 11)
                
            # Subtitle background style: translucent, solid, box, pill, none
            bg_clean = (bg_style or "translucent").lower().strip()
            if bg_clean in ("translucent", "box"):
                draw.rounded_rectangle(
                    [box_x, box_y, box_x + box_w, box_y + box_h],
                    radius=18,
                    fill=(10, 15, 28, 200),
                    outline=(255, 255, 255, 60),
                    width=2
                )
            elif bg_clean in ("solid", "dark"):
                draw.rounded_rectangle(
                    [box_x, box_y, box_x + box_w, box_y + box_h],
                    radius=18,
                    fill=(5, 8, 18, 245),
                    outline=(255, 255, 255, 100),
                    width=2
                )
            elif bg_clean == "pill":
                draw.rounded_rectangle(
                    [box_x, box_y, box_x + box_w, box_y + box_h],
                    radius=box_h // 2,
                    fill=(0, 0, 0, 210),
                    outline=(59, 130, 246, 180),
                    width=2
                )

            curr_y = box_y + sub_pad_y
            for i, line in enumerate(lines):
                lx = box_x + (box_w - line_widths[i]) / 2
                # High-contrast text drop shadow for maximum readability
                for ox, oy in [(-2, -2), (2, -2), (-2, 2), (2, 2), (0, 2), (0, -2), (1, 1), (-1, -1)]:
                    draw.text((lx + ox, curr_y + oy), line, fill=(0, 0, 0, 230), font=s_font)
                draw.text((lx, curr_y), line, fill=(*text_rgb, 255), font=s_font)
                curr_y += line_heights[i] + 8

        out_path = os.path.join(self.renders_dir, f"sub_{uuid.uuid4().hex}.png")
        overlay.save(out_path, "PNG")
        return out_path

    def build_camera_motion_filter(
        self,
        motion: str,
        w: int,
        h: int,
        duration: float,
        fps: int = 25
    ) -> str:
        """
        Builds optimized, frame-accurate FFmpeg zoompan and scaling filters for camera motions.
        """
        frames = max(25, int(duration * fps))
        
        # Safe zoom step
        step = 0.25 / frames
        
        if motion == "zoom_in":
            # Smooth zoom in to center from 1.0 to 1.25
            return f"scale=4000:-1,zoompan=z='min(zoom+{step:.5f},1.25)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}"
        elif motion == "zoom_out":
            # Smooth zoom out from 1.25 to 1.0
            return f"scale=4000:-1,zoompan=z='if(lte(zoom,1.0),1.25,max(1.001,zoom-{step:.5f}))':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}"
        elif motion == "pan_left":
            # Pan from right to left with 1.15x zoom
            return f"scale=4000:-1,zoompan=z=1.18:d={frames}:x='if(lte(on,1),(iw-iw/zoom),max(0,x-(iw-iw/zoom)/{frames}))':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}"
        elif motion == "pan_right":
            # Pan from left to right with 1.15x zoom
            return f"scale=4000:-1,zoompan=z=1.18:d={frames}:x='if(lte(on,1),0,min(iw-iw/zoom,x+(iw-iw/zoom)/{frames}))':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}"
        elif motion == "pan_up":
            # Pan from bottom to top
            return f"scale=4000:-1,zoompan=z=1.18:d={frames}:x='iw/2-(iw/zoom/2)':y='if(lte(on,1),(ih-ih/zoom),max(0,y-(ih-ih/zoom)/{frames}))':s={w}x{h}:fps={fps}"
        elif motion == "pan_down":
            # Pan from top to bottom
            return f"scale=4000:-1,zoompan=z=1.18:d={frames}:x='iw/2-(iw/zoom/2)':y='if(lte(on,1),0,min(ih-ih/zoom,y+(ih-ih/zoom)/{frames}))':s={w}x{h}:fps={fps}"
        elif motion == "ken_burns":
            # Diagonal pan + zoom
            return f"scale=4000:-1,zoompan=z='min(zoom+{step:.5f},1.22)':d={frames}:x='if(lte(on,1),0,min(iw-iw/zoom,x+(iw-iw/zoom)/{frames}))':y='if(lte(on,1),0,min(ih-ih/zoom,y+(ih-ih/zoom)/{frames}))':s={w}x{h}:fps={fps}"
        elif motion == "cinematic":
            # Slow subtle breathing drift
            half = max(1, frames // 2)
            return f"scale=4000:-1,zoompan=z='if(lte(on,{half}),1.0+0.12*(on/{half}),1.12-0.12*((on-{half})/{half}))':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps}"
        elif motion == "parallax_25d":
            # 2.5D Parallax: Dynamic focal zoom with subtle directional displacement
            return f"scale=4000:-1,zoompan=z='min(1.05+0.18*(on/{frames}),1.23)':d={frames}:x='(iw/2-(iw/zoom/2))+sin(on*0.05)*15':y='(ih/2-(ih/zoom/2))+cos(on*0.04)*10':s={w}x{h}:fps={fps}"
        else: # none / static
            return f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},format=yuv420p"

    def render_scene_clip(
        self,
        image_path: str,
        audio_path: Optional[str],
        duration: float,
        w: int,
        h: int,
        motion_mode: str = "camera",
        camera_motion: str = "zoom_in",
        ai_motion_style: str = "natural_flow",
        ai_intensity: str = "medium",
        headline: str = "",
        text: str = "",
        subtitle_settings: Optional[Dict[str, Any]] = None,
        aspect_ratio: str = "9:16"
    ) -> str:
        """
        Renders a single scene clip incorporating image animation, subtitles, and narration.
        """
        out_filename = f"scene_{uuid.uuid4().hex}.mp4"
        out_path = os.path.join(self.renders_dir, out_filename)
        
        # Audio length determines minimum duration
        audio_dur = video_service.get_audio_duration(audio_path) if audio_path else 0.0
        if audio_dur > 0:
            safe_dur = round(audio_dur + 0.35, 2)
        else:
            safe_dur = max(float(duration or 4.0), 2.5)

        # Build motion filter
        if motion_mode == "ai":
            # For AI motion mode: apply living fluid displacement with Ken Burns drift
            if ai_intensity == "high":
                motion_filter = f"scale=4000:-1,zoompan=z='min(1.08+0.20*(on/{int(safe_dur*25)}),1.28)':d={int(safe_dur*25)}:x='iw/2-(iw/zoom/2)+sin(on*0.08)*20':y='ih/2-(ih/zoom/2)+cos(on*0.06)*15':s={w}x{h}:fps=25"
            elif ai_intensity == "low":
                motion_filter = f"scale=4000:-1,zoompan=z='min(1.02+0.08*(on/{int(safe_dur*25)}),1.10)':d={int(safe_dur*25)}:x='iw/2-(iw/zoom/2)+sin(on*0.03)*8':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps=25"
            else: # medium
                motion_filter = f"scale=4000:-1,zoompan=z='min(1.05+0.14*(on/{int(safe_dur*25)}),1.19)':d={int(safe_dur*25)}:x='iw/2-(iw/zoom/2)+sin(on*0.05)*12':y='ih/2-(ih/zoom/2)+cos(on*0.04)*8':s={w}x{h}:fps=25"
        else:
            motion_filter = self.build_camera_motion_filter(camera_motion, w, h, safe_dur)

        # Generate subtitle overlay PNG if enabled
        sub_overlay_path = None
        if subtitle_settings and subtitle_settings.get("subtitles_enabled", True) and (text or headline):
            sub_overlay_path = self.create_subtitle_overlay_image(
                headline=headline,
                text=text,
                width=w,
                height=h,
                font_name=subtitle_settings.get("subtitle_font", "Inter"),
                font_size=subtitle_settings.get("subtitle_size", 32),
                font_color=subtitle_settings.get("subtitle_color", "#FFFFFF"),
                bg_style=subtitle_settings.get("subtitle_bg", "box"),
                position=subtitle_settings.get("subtitle_position", "bottom"),
                aspect_ratio=aspect_ratio
            )

        # Construct FFmpeg command
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", os.path.abspath(image_path)]
        
        # Audio input (or silent fallback if no audio provided)
        if audio_path and os.path.exists(audio_path):
            cmd.extend(["-i", os.path.abspath(audio_path)])
        else:
            cmd.extend(["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"])

        # Subtitle overlay input if present
        if sub_overlay_path and os.path.exists(sub_overlay_path):
            cmd.extend(["-i", os.path.abspath(sub_overlay_path)])
            filter_complex = f"[0:v]{motion_filter}[bg];[bg][2:v]overlay=0:0:format=auto[v];[1:a]apad=whole_dur={safe_dur:.2f}[a]"
        else:
            filter_complex = f"[0:v]{motion_filter}[v];[1:a]apad=whole_dur={safe_dur:.2f}[a]"

        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-t", f"{safe_dur:.2f}",
            "-movflags", "+faststart",
            out_path
        ])

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        finally:
            if sub_overlay_path and os.path.exists(sub_overlay_path):
                try:
                    os.remove(sub_overlay_path)
                except Exception:
                    pass

        return out_path

    def assemble_final_video(
        self,
        scene_video_paths: List[str],
        transitions: List[str],
        transition_durations: List[float],
        bg_music_path: Optional[str] = None,
        bg_music_volume: float = 0.18,
        voice_volume: float = 1.0,
        output_filename: Optional[str] = None
    ) -> str:
        """
        Chains rendered scenes with genuine xfade transitions and mixes background music.
        """
        if not scene_video_paths:
            raise ValueError("No scene clips provided for assembly.")

        if not output_filename:
            output_filename = f"image_to_video_{uuid.uuid4().hex}.mp4"
        final_output_path = os.path.join(self.renders_dir, output_filename)

        # Single scene case
        if len(scene_video_paths) == 1:
            if bg_music_path and os.path.exists(bg_music_path):
                # Mix with music
                cmd = [
                    "ffmpeg", "-y",
                    "-i", os.path.abspath(scene_video_paths[0]),
                    "-stream_loop", "-1", "-i", os.path.abspath(bg_music_path),
                    "-filter_complex", f"[0:a]volume={voice_volume:.2f}[va];[1:a]volume={bg_music_volume:.2f}[ba];[va][ba]amix=inputs=2:duration=first:dropout_transition=2[aout]",
                    "-map", "0:v",
                    "-map", "[aout]",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-movflags", "+faststart",
                    final_output_path
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return final_output_path
            else:
                shutil.copy2(scene_video_paths[0], final_output_path)
                return final_output_path

        # Multi-scene case: inspect scene durations
        durations = []
        for p in scene_video_paths:
            d = video_service.get_audio_duration(p)
            durations.append(max(d, 2.0))

        # Build xfade filter chain
        # Supported xfade map
        xfade_map = {
            "fade": "fade",
            "crossfade": "fade",
            "slide_left": "slideleft",
            "slide_right": "slideright",
            "slide_up": "slideup",
            "slide_down": "slidedown",
            "zoom": "zoomin",
            "dissolve": "dissolve",
            "blur": "radial",
            "circle": "circlecrop",
            "wipe_left": "wipeleft"
        }

        # Check total duration and calculate transition offsets
        inputs_cmd = []
        for p in scene_video_paths:
            inputs_cmd.extend(["-i", os.path.abspath(p)])

        video_filter_parts = []
        audio_filter_parts = []
        
        current_offset = durations[0]
        prev_v = "[0:v]"
        prev_a = "[0:a]"

        for i in range(1, len(scene_video_paths)):
            t_name = xfade_map.get(transitions[i - 1], "fade") if i - 1 < len(transitions) else "fade"
            t_dur = transition_durations[i - 1] if i - 1 < len(transition_durations) else 0.8
            t_dur = min(t_dur, min(durations[i-1], durations[i]) * 0.45) # Never exceed 45% of scene duration
            
            offset = max(0.1, current_offset - t_dur)
            out_v = f"[v{i}]"
            out_a = f"[a{i}]"

            video_filter_parts.append(f"{prev_v}[{i}:v]xfade=transition={t_name}:duration={t_dur:.2f}:offset={offset:.2f}{out_v}")
            audio_filter_parts.append(f"{prev_a}[{i}:a]acrossfade=d={t_dur:.2f}{out_a}")

            current_offset = offset + durations[i]
            prev_v = out_v
            prev_a = out_a

        full_filter_str = ";".join(video_filter_parts + audio_filter_parts)

        # Check if background music needs to be mixed
        if bg_music_path and os.path.exists(bg_music_path):
            music_idx = len(scene_video_paths)
            inputs_cmd.extend(["-stream_loop", "-1", "-i", os.path.abspath(bg_music_path)])
            full_filter_str += f";{prev_a}volume={voice_volume:.2f}[mva];[{music_idx}:a]volume={bg_music_volume:.2f}[mba];[mva][mba]amix=inputs=2:duration=first:dropout_transition=2[final_a]"
            final_a_label = "[final_a]"
        else:
            final_a_label = prev_a

        cmd = [
            "ffmpeg", "-y",
            *inputs_cmd,
            "-filter_complex", full_filter_str,
            "-map", prev_v,
            "-map", final_a_label,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            final_output_path
        ]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return final_output_path
        except subprocess.CalledProcessError as e:
            print(f"[ImageToVideoService] xfade assembly failed ({e.stderr.decode() if e.stderr else 'error'}), using concat fallback...")
            # Safe concatenation fallback
            return video_service.concatenate_scenes(scene_video_paths, output_filename=output_filename)

    def generate_srt_subtitles(self, scenes: List[Dict[str, Any]], durations: List[float]) -> str:
        """Generates standard RFC SRT subtitle text from scene narrations."""
        srt_lines = []
        curr_time = 0.0

        def fmt_time(seconds: float) -> str:
            hrs = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            millis = int((seconds - int(seconds)) * 1000)
            return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

        for idx, sc in enumerate(scenes, 1):
            text = (sc.get("text") or sc.get("headline") or "").strip()
            if not text:
                curr_time += durations[idx - 1] if idx - 1 < len(durations) else 4.0
                continue
                
            dur = durations[idx - 1] if idx - 1 < len(durations) else 4.0
            start_str = fmt_time(curr_time)
            end_str = fmt_time(curr_time + dur - 0.2)
            
            srt_lines.append(f"{idx}")
            srt_lines.append(f"{start_str} --> {end_str}")
            srt_lines.append(text)
            srt_lines.append("")
            
            curr_time += dur

        return "\n".join(srt_lines)

    def generate_script_for_images(
        self,
        topic: str = "",
        tone: str = "Inspiring",
        scenes_count: int = 5,
        images_info: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generates an engaging, cohesive scene-by-scene voiceover script for uploaded images.
        Supports Groq LLM if GROQ_API_KEY is configured, with fast Pollinations.ai fallback,
        and high-quality rule-based contextual fallback to ensure 100% reliable generation.
        """
        clean_topic = (topic or "").strip()
        if not clean_topic and images_info:
            extracted_names = []
            for item in images_info:
                fn = item.get("filename") or ""
                no_ext = os.path.splitext(fn)[0]
                cleaned = re.sub(r'^[a-f0-9]{8,16}_', '', no_ext)
                cleaned = re.sub(r'[_\W]+', ' ', cleaned).strip()
                if cleaned and not cleaned.lower().startswith("temp") and not re.match(r'^(image|img|\d+)$', cleaned.lower()):
                    extracted_names.append(cleaned.title())
            if extracted_names:
                clean_topic = ", ".join(list(dict.fromkeys(extracted_names))[:3])
        
        if not clean_topic:
            clean_topic = "A Captivating Visual Journey"

        scenes_count = max(1, min(20, scenes_count))
        
        # 1. Try Groq if key exists
        groq_key = os.getenv("GROQ_API_KEY", "")
        if groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=groq_key)
                system_prompt = (
                    "You are an elite video scriptwriter and voiceover narrator. "
                    "Write spoken-word narration for video scenes. "
                    "Output strictly a valid raw JSON object only."
                )
                user_prompt = f"""Write an engaging voiceover script for {scenes_count} scenes on the topic: "{clean_topic}".
Tone: {tone}.

For each scene from 1 to {scenes_count}:
- 'headline': 2 to 4 words punchy headline.
- 'text': 2 to 3 natural spoken sentences (15-25 words) that flow smoothly into the next scene.

Return strictly valid JSON:
{{
  "topic": "{clean_topic}",
  "scenes": [
    {{"scene_index": 1, "headline": "Headline", "text": "Narration text..."}}
  ]
}}"""
                resp = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                data = json.loads(resp.choices[0].message.content)
                if data and "scenes" in data and len(data["scenes"]) > 0:
                    return {
                        "success": True,
                        "topic": clean_topic,
                        "scenes": data["scenes"][:scenes_count]
                    }
            except Exception as e:
                print(f"[ImageToVideoService] Groq script gen note: {e}")

        # 2. Try Pollinations.ai fast JSON
        try:
            system_prompt = (
                "You are an elite video scriptwriter and voiceover narrator. "
                "Write spoken-word narration for video scenes. Output valid JSON only."
            )
            user_prompt = f"""Write an engaging voiceover script for {scenes_count} scenes on the topic: "{clean_topic}".
Tone: {tone}.

For each scene from 1 to {scenes_count}:
- 'headline': 2 to 4 words headline.
- 'text': 2 to 3 natural spoken sentences (15-25 words) suited for voiceover.

Return strictly valid JSON:
{{
  "topic": "{clean_topic}",
  "scenes": [
    {{"scene_index": 1, "headline": "Headline", "text": "Narration text..."}}
  ]
}}"""
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "model": "openai-fast",
                "jsonMode": True
            }
            res = requests.post("https://text.pollinations.ai/", json=payload, timeout=20)
            if res.status_code == 200:
                raw = res.text.strip()
                if "```" in raw:
                    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
                    if m:
                        raw = m.group(1).strip()
                parsed = json.loads(raw)
                if parsed and "scenes" in parsed and len(parsed["scenes"]) > 0:
                    return {
                        "success": True,
                        "topic": clean_topic,
                        "scenes": parsed["scenes"][:scenes_count]
                    }
        except Exception as e:
            print(f"[ImageToVideoService] Pollinations script gen note: {e}")

        # 3. Contextual Rule-Based Fallback (guarantees 100% reliable output)
        fallback_scenes = []
        phase_names = [
            ("Opening Discovery", f"Welcome to this captivating look at {clean_topic}. Every detail invites us to pause, observe, and experience something truly extraordinary."),
            ("Deeper Perspective", f"Taking a closer perspective, {clean_topic} reveals timeless grace and remarkable presence that captures the imagination."),
            ("Harmonious Focus", f"The serene atmosphere surrounding {clean_topic} inspires quiet reflection and a deep sense of balance."),
            ("Inspiring Moment", f"Notice the intricate character and beauty that make this moment so memorable and inspiring."),
            ("Lasting Impression", f"As our journey concludes, the lasting spirit of {clean_topic} remains with us, reminding us of the wonder in our world.")
        ]
        
        for idx in range(1, scenes_count + 1):
            phase_idx = (idx - 1) % len(phase_names)
            hl, txt = phase_names[phase_idx]
            fallback_scenes.append({
                "scene_index": idx,
                "headline": f"{hl}",
                "text": txt
            })

        return {
            "success": True,
            "topic": clean_topic,
            "scenes": fallback_scenes
        }

    def rewrite_scene_script(
        self,
        scene_index: int = 1,
        current_text: str = "",
        topic: str = "",
        tone: str = "Inspiring",
        filename: str = ""
    ) -> Dict[str, Any]:
        """Rewrites or polishes an individual scene's script with AI."""
        context_topic = topic.strip() if topic else "this visual scene"
        prompt = f"Rewrite and polish this voiceover narration for scene {scene_index} of a video about '{context_topic}'. Current text: '{current_text}'. Tone: {tone}. Keep it natural, punchy (15-25 words), and spoken-word friendly. Return JSON: {{\"headline\": \"...\", \"text\": \"...\"}}"
        
        try:
            payload = {
                "messages": [
                    {"role": "system", "content": "You are a professional video script editor. Output valid JSON only with 'headline' and 'text'."},
                    {"role": "user", "content": prompt}
                ],
                "model": "openai-fast",
                "jsonMode": True
            }
            res = requests.post("https://text.pollinations.ai/", json=payload, timeout=15)
            if res.status_code == 200:
                raw = res.text.strip()
                if "```" in raw:
                    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
                    if m:
                        raw = m.group(1).strip()
                parsed = json.loads(raw)
                if parsed and "text" in parsed:
                    return {
                        "success": True,
                        "headline": parsed.get("headline", f"Scene {scene_index}"),
                        "text": parsed.get("text", current_text)
                    }
        except Exception as e:
            print(f"[ImageToVideoService] Rewrite note: {e}")

        # Fallback polish
        return {
            "success": True,
            "headline": f"Scene {scene_index} Focus",
            "text": f"Experience the captivating presence of {context_topic}, creating an unforgettable impression of peace and beauty."
        }

image_to_video_service = ImageToVideoService()

