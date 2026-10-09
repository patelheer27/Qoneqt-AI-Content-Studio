import asyncio
import edge_tts
import os
import uuid

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

    async def _generate_audio_edge(self, text: str, voice: str) -> str:
        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(self.output_dir, filename)
        
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(filepath)
        return filepath
        
    def generate_voiceover(self, text: str, voice_style: str = "Default", language: str = "English") -> str:
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
            "Default": "en-US-AriaNeural"
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
            print(f"[TTSService] Generating English audio using voice='{voice}'...")
            filepath = asyncio.run(self._generate_audio_edge(text, voice))
            return filepath
        except Exception as e:
            print(f"[TTSService] Error with voice {voice}: {e}, trying fallback {fallback_voice}")
            filepath = asyncio.run(self._generate_audio_edge(text, fallback_voice))
            return filepath

tts_service = TTSService()
