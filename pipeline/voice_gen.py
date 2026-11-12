import os
import asyncio
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple
import edge_tts
from config import FFMPEG_PATH, VOICE_PRESETS

def get_audio_duration(audio_path: Path) -> float:
    """
    คำนวณความยาวไฟล์เสียงเป็นวินาทีโดยใช้ FFmpeg
    """
    cmd = [FFMPEG_PATH, "-i", str(audio_path)]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True, encoding="utf-8", errors="ignore")
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", result.stderr)
    if match:
        hours = float(match.group(1))
        minutes = float(match.group(2))
        seconds = float(match.group(3))
        return hours * 3600 + minutes * 60 + seconds
    return 5.0 # fallback

async def _synthesize_edge_tts(text: str, voice: str, output_path: Path):
    """รัน Edge TTS แบบ asynchronous"""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))

def generate_voice_clip(text: str, output_path: Path, voice: str = None) -> float:
    """
    สร้างเสียงพากย์ 1 คลิป และคืนค่าความยาวของเสียง (วินาที)
    """
    if not voice:
        voice = VOICE_PRESETS["male"]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_synthesize_edge_tts(text, voice, output_path))
    return get_audio_duration(output_path)

def format_timestamp(seconds: float) -> str:
    """แปลงวินาทีเป็นรูปแบบ SRT timestamp (HH:MM:SS,mmm)"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def generate_scene_voices(
    scenes: List[Dict[str, Any]],
    output_dir: Path,
    voice_type: str = "male"
) -> Tuple[List[Path], List[float], Path]:
    """
    สร้างเสียงพากย์ครบทุกฉาก พร้อมไฟล์ Subtitle (.srt)
    """
    selected_voice = VOICE_PRESETS.get(voice_type, VOICE_PRESETS["male"])
    audio_paths = []
    durations = []

    srt_lines = []
    current_time = 0.0

    print(f"🎙️ [Voice AI] กำลังสร้างเสียงพากย์ด้วยโมเดล: {selected_voice}")

    for idx, scene in enumerate(scenes, start=1):
        scene_id = scene.get("scene_id", idx)
        narration = scene.get("narration", "")
        audio_file = output_dir / f"scene_{scene_id:02d}.mp3"

        duration = generate_voice_clip(narration, audio_file, selected_voice)
        audio_paths.append(audio_file)
        durations.append(duration)

        # สร้างข้อมูล Subtitle SRT
        start_ts = format_timestamp(current_time)
        end_ts = format_timestamp(current_time + duration)

        srt_lines.append(f"{idx}")
        srt_lines.append(f"{start_ts} --> {end_ts}")
        srt_lines.append(f"{narration}\n")

        current_time += duration

    # บันทึกไฟล์ .srt
    srt_path = output_dir / "subtitles.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))

    return audio_paths, durations, srt_path
