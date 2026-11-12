import os
import subprocess
from pathlib import Path
from typing import List
from config import FFMPEG_PATH, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS

def assemble_scene_clip(
    image_path: Path,
    audio_path: Path,
    duration: float,
    output_clip_path: Path
) -> Path:
    """
    สร้างคลิปวิดีโอ 1 ฉากแนวตั้ง 9:16 (1080x1920) พร้อม Effect Ken Burns (Zoom ช้าๆ)
    """
    output_clip_path.parent.mkdir(parents=True, exist_ok=True)
    frames = int((duration + 0.3) * VIDEO_FPS)

    # FFmpeg Filter: ยืดภาพให้พอดี 1080x1920 พร้อม Slow Zoom-in ให้ดูมีชีวิตชีวา
    filter_complex = (
        f"[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
        f"zoompan=z='min(zoom+0.0008,1.15)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={VIDEO_FPS}[v]"
    )

    cmd = [
        FFMPEG_PATH, "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-i", str(audio_path),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(output_clip_path)
    ]

    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore")
    if res.returncode != 0:
        # Fallback to simple scaling without zoompan if complex filter fails
        fallback_filter = (
            f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT}"
        )
        fallback_cmd = [
            FFMPEG_PATH, "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-i", str(audio_path),
            "-vf", fallback_filter,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-shortest",
            str(output_clip_path)
        ]
        subprocess.run(fallback_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)

    return output_clip_path

def burn_subtitles(
    input_video: Path,
    srt_path: Path,
    output_video: Path
) -> Path:
    """
    ใส่ซับไตเติลภาษาไทยลงบนวิดีโอ (สไตล์ Reels: ตัวหนังสือขาว ขอบดำ หนา ชัดเจน)
    """
    # Format Windows path for FFmpeg subtitles filter
    srt_escaped = str(srt_path).replace("\\", "/").replace(":", "\\:")
    subtitle_style = (
        "FontName=Tahoma,"
        "FontSize=16,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BorderStyle=3,"
        "Outline=2.5,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=180"
    )

    cmd = [
        FFMPEG_PATH, "-y",
        "-i", str(input_video),
        "-vf", f"subtitles='{srt_escaped}':force_style='{subtitle_style}'",
        "-c:v", "libx264",
        "-c:a", "copy",
        str(output_video)
    ]

    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore")
    if res.returncode != 0:
        print("[Notice] ไม่สามารถ Render ซับไตเติลฝังในวิดีโอได้ ส่งออกเป็นวิดีโอพร้อมไฟล์ .srt แทน")
        return input_video

    return output_video

def assemble_final_reel(
    scene_clips: List[Path],
    srt_path: Path,
    final_output_path: Path
) -> Path:
    """
    รวมทุกคลิปเข้าด้วยกันเป็นไฟล์ Reels .mp4 ฉบับสมบูรณ์
    """
    final_output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_concat_file = final_output_path.parent / "concat_list.txt"
    merged_raw_path = final_output_path.parent / "merged_raw.mp4"

    # เขียนไฟล์รายการคลิปสำหรับ FFmpeg concat
    with open(temp_concat_file, "w", encoding="utf-8") as f:
        for clip in scene_clips:
            # ใช้ absolute path พร้อม escape single quotes
            clean_path = str(clip.resolve()).replace("\\", "/")
            f.write(f"file '{clean_path}'\n")

    print("🎞️ [Video Engine] กำลังรวมทุกฉากเข้าด้วยกัน...")
    concat_cmd = [
        FFMPEG_PATH, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(temp_concat_file),
        "-c", "copy",
        str(merged_raw_path)
    ]
    subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)

    # ใส่ Subtitle ลงในวิดีโอ
    print("📝 [Subtitle Engine] กำลังฝังซับไตเติลภาษาไทยลงบนวิดีโอ...")
    final_path = burn_subtitles(merged_raw_path, srt_path, final_output_path)

    # ล้างไฟล์ชั่วคราว
    try:
        if temp_concat_file.exists():
            temp_concat_file.unlink()
        if merged_raw_path.exists() and final_path != merged_raw_path:
            merged_raw_path.unlink()
    except Exception:
        pass

    return final_path
