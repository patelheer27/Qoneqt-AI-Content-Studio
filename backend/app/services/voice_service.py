import asyncio
import logging
import os
import subprocess
import wave
import struct
from pathlib import Path
from typing import List, Optional
from app.config import settings
from app.models.scene import Scene

logger = logging.getLogger(__name__)

def get_ffmpeg_binary() -> str:
    import shutil
    bin_path = shutil.which("ffmpeg")
    if bin_path:
        return bin_path
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

def get_audio_duration(file_path: Path) -> float:
    """Uses ffmpeg or fallback to estimate audio file duration"""
    try:
        import re
        ffmpeg_bin = get_ffmpeg_binary()
        cmd = [ffmpeg_bin, "-i", str(file_path)]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # ffmpeg outputs info to stderr
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
        if match:
            h, m, s = match.groups()
            duration = int(h) * 3600 + int(m) * 60 + float(s)
            # Add 0.3s padding to prevent abrupt cutting
            return duration + 0.3
    except Exception as e:
        logger.warning(f"Error getting audio duration: {e}")

    # Fallback estimation based on file size or default
    return 4.5

def generate_silent_audio(output_path: Path, duration: float = 4.0) -> Path:
    """Generates a clean silent audio WAV file using standard python wave module"""
    sample_rate = 24000
    num_samples = int(sample_rate * duration)
    wav_path = output_path.with_suffix(".wav")

    with wave.open(str(wav_path), "w") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        # Write zeroed audio samples
        data = struct.pack("<" + "h" * num_samples, *([0] * num_samples))
        wav_file.writeframes(data)

    return wav_path

async def synthesize_edge_tts(text: str, output_path: Path, voice: str = "en-US-ChristopherNeural") -> bool:
    """Synthesizes high quality neural speech using edge-tts"""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await asyncio.wait_for(communicate.save(str(output_path)), timeout=10.0)
        if output_path.exists() and output_path.stat().st_size > 100:
            return True
    except asyncio.TimeoutError:
        logger.warning("edge-tts synthesis timed out (likely IP block on host). Falling back to gTTS.")
    except Exception as e:
        logger.warning(f"edge-tts synthesis failed: {e}")
    return False

def synthesize_gtts(text: str, output_path: Path) -> bool:
    """Fallback speech synthesis using gTTS"""
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(str(output_path))
        if output_path.exists() and output_path.stat().st_size > 100:
            return True
    except Exception as e:
        logger.warning(f"gTTS synthesis failed: {e}")
    return False

class VoiceService:
    @staticmethod
    async def generate_scene_audio(
        project_id: str,
        scene: Scene
    ) -> tuple[Path, float]:
        """
        Synthesizes speech for scene narration.
        Returns (audio_path, duration_in_seconds).
        """
        output_filename = f"scene_{project_id}_{scene.scene_number}.mp3"
        output_path = settings.AUDIO_DIR / output_filename

        text = scene.narration.strip()
        if not text:
            text = scene.on_screen_text

        # If VOICE_ENABLED is False or in forced silent mode
        if not settings.VOICE_ENABLED:
            logger.info(f"VOICE_ENABLED is false. Generating silent track for scene {scene.scene_number}")
            silent_path = generate_silent_audio(output_path, scene.duration)
            return silent_path, scene.duration

        # 1. Try edge-tts (ultra-realistic neural voice)
        success = await synthesize_edge_tts(text, output_path)

        # 2. Try gTTS fallback
        if not success:
            success = synthesize_gtts(text, output_path)

        # 3. Graceful fallback to silence if offline
        if not success or not output_path.exists():
            logger.warning(f"All TTS services unavailable. Generating silent track for scene {scene.scene_number}")
            silent_path = generate_silent_audio(output_path, scene.duration)
            return silent_path, scene.duration

        duration = get_audio_duration(output_path)
        # Ensure at least 2.5s duration
        duration = max(2.5, duration)
        return output_path, duration

    @classmethod
    async def generate_all_scene_audio(
        cls,
        project_id: str,
        scenes: List[Scene]
    ) -> List[tuple[Path, float]]:
        """
        Synthesizes audio for all scenes in parallel or sequence.
        """
        results = []
        for sc in scenes:
            path, dur = await cls.generate_scene_audio(project_id, sc)
            sc.audio_path = str(path)
            sc.duration = round(dur, 2)
            results.append((path, dur))
        return results
