from pathlib import Path
from typing import List, Tuple

def format_srt_time(seconds: float) -> str:
    """Formats seconds into SRT timestamp HH:MM:SS,mmm"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def create_srt_file(cues: List[Tuple[float, float, str]], output_path: Path) -> Path:
    """
    Creates an SRT subtitle file from a list of (start_seconds, end_seconds, text).
    """
    lines = []
    for idx, (start, end, text) in enumerate(cues, start=1):
        lines.append(str(idx))
        lines.append(f"{format_srt_time(start)} --> {format_srt_time(end)}")
        lines.append(text.strip())
        lines.append("")

    content = "\n".join(lines)
    output_path.write_text(content, encoding="utf-8")
    return output_path

def create_ass_file(cues: List[Tuple[float, float, str]], output_path: Path) -> Path:
    """
    Creates an Advanced SubStation Alpha (.ass) subtitle file formatted
    for TikTok/Reels style vertical videos (large bold font, yellow/white text, shadow/outline).
    """
    def format_ass_time(seconds: float) -> str:
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int((seconds - int(seconds)) * 100)
        return f"{hrs:d}:{mins:02d}:{secs:02d}.{centis:02d}"

    header = """[Script Info]
Title: Qoneqt Dynamic Captions
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,58,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,3,2,60,60,320,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for start, end, text in cues:
        # Wrap long captions if needed
        clean_text = text.replace("\n", " ").strip()
        events.append(f"Dialogue: 0,{format_ass_time(start)},{format_ass_time(end)},Default,,0,0,0,,{clean_text}")

    full_content = header + "\n".join(events) + "\n"
    output_path.write_text(full_content, encoding="utf-8")
    return output_path
