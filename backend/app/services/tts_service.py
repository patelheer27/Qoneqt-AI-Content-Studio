import asyncio
import edge_tts
import os
import uuid
import subprocess
import shutil

class TTSService:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.output_dir = os.path.join(base_dir, "storage", "assets", "audio")
        os.makedirs(self.output_dir, exist_ok=True)
        
    def get_available_voices(self) -> list[dict]:
        return [
            {"id": "en-US-AriaNeural", "name": "Aria", "gender": "Female", "style": "Energetic & Modern", "accent": "US", "language": "English"},
            {"id": "en-US-GuyNeural", "name": "Guy", "gender": "Male", "style": "Professional & Confident", "accent": "US", "language": "English"},
            {"id": "en-US-JennyNeural", "name": "Jenny", "gender": "Female", "style": "Warm & Friendly", "accent": "US", "language": "English"},
            {"id": "en-US-ChristopherNeural", "name": "Christopher", "gender": "Male", "style": "Deep & Narrative", "accent": "US", "language": "English"},
            {"id": "en-US-EricNeural", "name": "Eric", "gender": "Male", "style": "Contemporary & Casual", "accent": "US", "language": "English"},
            {"id": "en-US-AnaNeural", "name": "Ana", "gender": "Female", "style": "Engaging & Youthful", "accent": "US", "language": "English"},
            {"id": "en-GB-SoniaNeural", "name": "Sonia", "gender": "Female", "style": "Sophisticated British", "accent": "GB", "language": "English"},
            {"id": "en-GB-RyanNeural", "name": "Ryan", "gender": "Male", "style": "Polished British", "accent": "GB", "language": "English"},
            {"id": "en-IN-NeerjaNeural", "name": "Neerja", "gender": "Female", "style": "Indian Expressive", "accent": "IN", "language": "English"},
            {"id": "en-IN-PrabhatNeural", "name": "Prabhat", "gender": "Male", "style": "Indian Professional", "accent": "IN", "language": "English"},
        ]

    async def _generate_audio_edge(self, text: str, voice: str, rate: str = "+18%") -> str:
        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(self.output_dir, filename)
        
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(filepath)
        return filepath

    def _speedup_audio_file(self, input_path: str, output_path: str, speed_factor: float = 1.18) -> str:
        """Applies FFmpeg atempo filter to accelerate audio to normal, energetic speaking speed."""
        try:
            cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-filter:a", f"atempo={speed_factor}",
                "-vn", output_path
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(input_path) and input_path != output_path:
                try:
                    os.remove(input_path)
                except Exception:
                    pass
            return output_path
        except Exception as err:
            print(f"[TTSService] ffmpeg audio speedup warning: {err}, falling back to original audio")
            if input_path != output_path and os.path.exists(input_path):
                shutil.copy2(input_path, output_path)
            return output_path
        
    def generate_voiceover(self, text: str, voice_style: str = "Default", language: str = "English", rate: str = "+18%") -> str:
        if not text or not text.strip():
            text = "Welcome to the video."

        is_male = any(kw in (voice_style or "").lower() for kw in ["male", "guy", "christopher", "eric", "ryan", "prabhat", "deep"])

        voice_map = {
            "Energetic Female": "en-US-AriaNeural",
            "Professional Male": "en-US-GuyNeural",
            "Warm Female": "en-US-JennyNeural",
            "Deep Male": "en-US-ChristopherNeural",
            "Contemporary Male": "en-US-EricNeural",
            "Engaging Female": "en-US-AnaNeural",
            "British Female": "en-GB-SoniaNeural",
            "British Male": "en-GB-RyanNeural",
            "Indian Female": "en-IN-NeerjaNeural",
            "Indian Male": "en-IN-PrabhatNeural",
            "Default": "en-US-GuyNeural" if is_male else "en-US-AriaNeural"
        }

        if voice_style in voice_map:
            voice = voice_map[voice_style]
        elif "Neural" in (voice_style or ""):
            voice = voice_style
        elif is_male:
            voice = "en-US-GuyNeural"
        else:
            voice = "en-US-AriaNeural"

        fallback_voice = "en-US-GuyNeural" if is_male else "en-US-AriaNeural"
        
        try:
            print(f"[TTSService] Generating English audio using voice='{voice}' at rate='{rate}'...")
            filepath = asyncio.run(self._generate_audio_edge(text, voice, rate=rate))
            return filepath
        except Exception as e:
            print(f"[TTSService] Error with voice {voice}: {e}, trying fallback {fallback_voice}")
            try:
                filepath = asyncio.run(self._generate_audio_edge(text, fallback_voice, rate=rate))
                return filepath
            except Exception as e2:
                print(f"[TTSService] Edge-TTS failed: {e2}. Attempting Google TTS (gTTS) fallback...")
                try:
                    from gtts import gTTS
                    filename = f"{uuid.uuid4().hex}.mp3"
                    filepath = os.path.join(self.output_dir, filename)
                    raw_filepath = os.path.join(self.output_dir, f"raw_{filename}")
                    tts = gTTS(text=text, lang="en")
                    tts.save(raw_filepath)
                    # gTTS default tempo is sluggish; speed it up with FFmpeg to normal conversational pace
                    self._speedup_audio_file(raw_filepath, filepath, speed_factor=1.18)
                    print(f"[TTSService] Successfully synthesized voiceover via gTTS (accelerated 1.18x): {filepath}")
                    return filepath
                except Exception as gtts_err:
                    print(f"[TTSService] gTTS fallback failed: {gtts_err}")
                    raise

tts_service = TTSService()
