import os
import sys
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Ensure console supports UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Load .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

# Output directories
OUTPUT_DIR = BASE_DIR / "output"
AUDIO_DIR = OUTPUT_DIR / "audio"
IMAGES_DIR = OUTPUT_DIR / "images"
VIDEOS_DIR = OUTPUT_DIR / "videos"

for d in [OUTPUT_DIR, AUDIO_DIR, IMAGES_DIR, VIDEOS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Video Specs (TikTok / Reels / Shorts 9:16)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30

# Voice Presets (Edge-TTS Free Neural Voices)
VOICE_PRESETS = {
    "male": "th-TH-NiwatNeural",         # ชาย เสียงสุขุม ทรงพลัง เหมาะกับเรื่องเล่า/ผี/ประวัติศาสตร์
    "female": "th-TH-PremwadeeNeural",   # หญิง เสียงอบอุ่น ชัดเจน เหมาะกับดราม่า/ความรู้
}

# Locate FFmpeg executable automatically
def get_ffmpeg_path() -> str:
    # 1. Check system PATH
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg
    # 2. Check imageio-ffmpeg bundled binary
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        raise RuntimeError("ไม่พบ FFmpeg ในระบบ กรุณาตรวจสอบว่าติดตั้ง imageio-ffmpeg แล้ว")

FFMPEG_PATH = get_ffmpeg_path()
