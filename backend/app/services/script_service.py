import re
from typing import List

class ScriptService:
    @staticmethod
    def estimate_narration_duration(text: str, words_per_minute: int = 145) -> float:
        """
        Estimates the speaking duration of a narration string in seconds.
        Standard conversational social media rate is ~140-150 wpm.
        """
        words = len(re.findall(r'\b\w+\b', text))
        seconds = (words / words_per_minute) * 60.0
        return max(2.5, round(seconds, 2))

    @staticmethod
    def balance_scene_durations(scenes_data: List[dict], total_target_duration: int) -> List[dict]:
        """
        Adjusts scene durations proportionally so they cleanly fit target duration.
        """
        if not scenes_data:
            return []
        
        raw_durations = [s.get("duration", 5.0) for s in scenes_data]
        total_raw = sum(raw_durations) or 1.0
        ratio = total_target_duration / total_raw

        for s in scenes_data:
            s["duration"] = round(s.get("duration", 5.0) * ratio, 1)

        return scenes_data
