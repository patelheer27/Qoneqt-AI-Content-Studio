import subprocess
import os
import uuid
import re

class VideoService:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.output_dir = os.path.join(base_dir, "storage", "renders")
        os.makedirs(self.output_dir, exist_ok=True)
        
    def get_audio_duration(self, audio_path: str) -> float:
        """Accurately calculates audio duration in seconds using ffmpeg probe."""
        try:
            cmd = ["ffmpeg", "-i", audio_path]
            p = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="ignore")
            m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", p.stderr)
            if m:
                hours, mins, secs = m.groups()
                return int(hours) * 3600 + int(mins) * 60 + float(secs)
        except Exception as e:
            print(f"[VideoService] Error determining audio duration: {e}")
        return 0.0

    def render_scene(self, media_path: str, audio_path: str, duration: float, aspect_ratio: str = "9:16") -> str:
        """Renders a single scene from an image or video clip and audio using FFmpeg without clipping speech."""
        scene_filename = f"scene_{uuid.uuid4().hex}.mp4"
        scene_filepath = os.path.join(self.output_dir, scene_filename)
        
        # Dimensions based on aspect ratio
        if aspect_ratio == "16:9":
            w, h = 1920, 1080
        elif aspect_ratio == "1:1":
            w, h = 1080, 1080
        elif aspect_ratio == "4:5":
            w, h = 1080, 1350
        else: # 9:16 default
            w, h = 1080, 1920

        # Calculate exact audio duration to guarantee speech is NEVER cut off in between
        audio_duration = self.get_audio_duration(audio_path)
        # Add a comfortable 0.45s breathing buffer after speech finishes
        safe_duration = max(float(duration or 0), audio_duration + 0.45, 3.0)

        is_video = any(media_path.lower().endswith(ext) for ext in [".mp4", ".mov", ".webm", ".avi", ".mkv"])
        
        # Ensure media covers 100% of the entire area edge-to-edge with no black borders (full-bleed coverage)
        vf_filter = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},format=yuv420p"

        if is_video:
            cmd = [
                "ffmpeg", "-y",
                "-stream_loop", "-1",
                "-i", media_path,
                "-i", audio_path,
                "-vf", vf_filter,
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-r", "25",
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "44100",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                "-t", f"{safe_duration:.2f}",
                scene_filepath
            ]
        else: # Image
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-framerate", "25",
                "-i", media_path,
                "-i", audio_path,
                "-vf", vf_filter,
                "-color_range", "1",
                "-colorspace", "bt709",
                "-color_primaries", "bt709",
                "-color_trc", "bt709",
                "-c:v", "libx264",
                "-preset", "medium",
                "-r", "25",
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "44100",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                "-t", f"{safe_duration:.2f}",
                scene_filepath
            ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return scene_filepath
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error: {e.stderr.decode()}")
            raise Exception("FFmpeg rendering failed")

    def concatenate_scenes(self, scene_paths: list[str], output_filename: str = None) -> str:
        """Concatenates multiple scene MP4s into a final video."""
        if not output_filename:
            output_filename = f"final_{uuid.uuid4().hex}.mp4"
            
        output_filepath = os.path.join(self.output_dir, output_filename)
        
        # Create a text file with list of files to concatenate
        list_file = os.path.join(self.output_dir, f"list_{uuid.uuid4().hex}.txt")
        with open(list_file, "w") as f:
            for path in scene_paths:
                safe_path = os.path.abspath(path).replace("\\", "/")
                f.write(f"file '{safe_path}'\n")
                
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-movflags", "+faststart",
            output_filepath
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if os.path.exists(list_file):
                os.remove(list_file)
            return output_filepath
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error: {e.stderr.decode()}")
            raise Exception("FFmpeg concatenation failed")

video_service = VideoService()
