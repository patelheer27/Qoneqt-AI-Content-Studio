import os
import shutil
import subprocess
import logging
from pathlib import Path
from typing import List, Tuple
from app.config import settings
from app.models.scene import Scene
from app.utils.subtitles import create_srt_file, create_ass_file

logger = logging.getLogger(__name__)

def get_ffmpeg_binary() -> str:
    """Returns the executable path for ffmpeg"""
    bin_path = shutil.which("ffmpeg")
    if bin_path:
        return bin_path
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

class VideoService:
    @staticmethod
    def create_scene_segment(
        image_path: Path,
        audio_path: Path,
        duration: float,
        output_segment_path: Path
    ) -> Path:
        """
        Creates an individual scene video segment (1080x1920 MP4)
        combining static graphic image and narration audio.
        """
        ffmpeg_bin = get_ffmpeg_binary()
        output_segment_path.parent.mkdir(parents=True, exist_ok=True)

        # Video filters: ensure 1080x1920, 30fps
        vf_filter = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,format=yuv420p"

        cmd = [
            ffmpeg_bin, "-y",
            "-loop", "1",
            "-framerate", "30",
            "-i", str(image_path),
            "-i", str(audio_path),
            "-vf", vf_filter,
            "-af", "apad",
            "-t", f"{duration:.3f}",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            "-pix_fmt", "yuv420p",
            str(output_segment_path)
        ]

        logger.info(f"Rendering scene segment: {output_segment_path.name}")
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            logger.error(f"FFmpeg error on segment: {proc.stderr}")
            raise RuntimeError(f"FFmpeg failed to create scene segment: {proc.stderr}")

        return output_segment_path

    @classmethod
    def compose_full_video(
        cls,
        project_id: str,
        scenes: List[Scene]
    ) -> tuple[Path, Path]:
        """
        Composites full vertical MP4 video with audio and synchronized captions.
        Returns (mp4_path, srt_path).
        """
        ffmpeg_bin = get_ffmpeg_binary()
        temp_dir = settings.VIDEOS_DIR / f"temp_{project_id}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        segment_paths: List[Path] = []
        cues: List[Tuple[float, float, str]] = []
        current_time = 0.0

        for sc in scenes:
            img_p = Path(sc.visual_path)
            aud_p = Path(sc.audio_path)
            seg_p = temp_dir / f"seg_{sc.scene_number}.mp4"

            # Create video segment
            cls.create_scene_segment(img_p, aud_p, sc.duration, seg_p)
            segment_paths.append(seg_p)

            # Record subtitle cue
            start_t = current_time
            end_t = current_time + sc.duration
            cues.append((start_t, end_t, sc.narration))
            current_time = end_t

        # Generate SRT and ASS subtitles
        srt_path = settings.CAPTIONS_DIR / f"{project_id}.srt"
        ass_path = settings.CAPTIONS_DIR / f"{project_id}.ass"
        create_srt_file(cues, srt_path)
        create_ass_file(cues, ass_path)

        # Concatenate segments using concat demuxer
        concat_txt = temp_dir / "concat_list.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for seg in segment_paths:
                # FFmpeg concat file syntax with escaped backslashes
                clean_path = str(seg.resolve()).replace("\\", "/")
                f.write(f"file '{clean_path}'\n")

        final_mp4_path = settings.VIDEOS_DIR / f"{project_id}.mp4"

        # Concat command with faststart for HTML5 web streaming
        concat_cmd = [
            ffmpeg_bin, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "160k",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(final_mp4_path)
        ]

        logger.info(f"Concatenating {len(segment_paths)} scenes into final MP4: {final_mp4_path.name}")
        proc = subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            logger.error(f"FFmpeg concatenation failed: {proc.stderr}")
            raise RuntimeError(f"FFmpeg concatenation failed: {proc.stderr}")

        # Clean up temporary segments
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

        return final_mp4_path, srt_path
