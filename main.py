import os
import sys
import argparse
import json
import time
from pathlib import Path

# Add current dir to path and ensure UTF-8
sys.path.insert(0, str(Path(__file__).resolve().parent))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config import (
    GEMINI_API_KEY,
    OUTPUT_DIR,
    AUDIO_DIR,
    IMAGES_DIR,
    VIDEOS_DIR,
    VOICE_PRESETS
)
from pipeline.script_gen import generate_reel_script
from pipeline.voice_gen import generate_scene_voices
from pipeline.image_gen import generate_scene_images
from pipeline.assembler import assemble_scene_clip, assemble_final_reel

def run_pipeline(
    topic: str,
    style: str = "horror",
    voice: str = "male",
    num_scenes: int = 5,
    preview_only: bool = False,
    api_key: str = None
):
    active_key = (api_key or "").strip() or GEMINI_API_KEY
    print("\n" + "=" * 60)
    print("🎬  AI REELS STUDIO - AUTOMATED PRODUCTION PIPELINE  🎬")
    print("=" * 60)
    print(f"📌 หัวข้อ:       {topic}")
    print(f"🎭 สไตล์:        {style}")
    print(f"🎙️ เสียงพากย์:    {voice} ({VOICE_PRESETS.get(voice, voice)})")
    print(f"🎞️ จำนวนฉาก:     {num_scenes} ฉาก")
    print("=" * 60 + "\n")

    start_time = time.time()

    # 1. ตรวจสอบ API Key
    if not active_key:
        print("❌ ข้อผิดพลาด: ไม่พบ GEMINI_API_KEY")
        print("💡 วิธีแก้ไข: ใส่ในไฟล์ .env หรือส่งผ่านพารามิเตอร์ --api-key (รับฟรีได้จาก https://aistudio.google.com/)")
        return

    # 2. สร้างบทละคร & สตอรี่บอร์ด
    print("🧠 [Step 1/4] กำลังเขียนบทละครและสตอรี่บอร์ดด้วย Gemini AI...")
    try:
        script_data = generate_reel_script(
            topic=topic,
            style=style,
            num_scenes=num_scenes,
            api_key=active_key
        )
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการสร้างบท: {e}")
        return

    # บันทึกบทเก็บไว้เป็น JSON
    script_file = OUTPUT_DIR / "current_script.json"
    with open(script_file, "w", encoding="utf-8") as f:
        json.dump(script_data, f, ensure_ascii=False, indent=2)

    print(f"✅ สร้างบทสำเร็จ: \"{script_data.get('title')}\"")
    print(f"🎯 Hook: {script_data.get('hook')}\n")

    scenes = script_data.get("scenes", [])
    if not scenes:
        print("❌ ไม่พบฉากในสคริปต์")
        return

    # 3. สร้างเสียงพากย์และซับไตเติล
    print("🎙️ [Step 2/4] กำลังสร้างเสียงพากย์ภาษาไทย และสร้างไฟล์ Subtitle (.srt)...")
    audio_paths, durations, srt_path = generate_scene_voices(
        scenes=scenes,
        output_dir=AUDIO_DIR,
        voice_type=voice
    )
    total_audio_duration = sum(durations)
    print(f"✅ บันทึกเสียงพากย์เสร็จสิ้น ความยาวรวม {total_audio_duration:.1f} วินาที\n")

    # 4. สร้างภาพประกอบ AI
    print("🎨 [Step 3/4] กำลังสร้างภาพประกอบ AI สไตล์ 9:16 สำหรับทุกฉาก...")
    image_paths = generate_scene_images(
        scenes=scenes,
        output_dir=IMAGES_DIR,
        api_key=active_key
    )
    print(f"✅ สร้างภาพครบ {len(image_paths)} ฉากแล้ว\n")

    if preview_only:
        print("⚡ [Preview Only] สร้างสคริปต์, เสียง และภาพเรียบร้อยแล้ว ข้ามขั้นตอนการตัดต่อวิดีโอ")
        print(f"📂 ไฟล์ทั้งหมดอยู่ในโฟลเดอร์: {OUTPUT_DIR.resolve()}")
        return

    # 5. ตัดต่อวิดีโอและฝังซับไตเติล
    print("🎞️ [Step 4/4] กำลังตัดต่อและเรนเดอร์วิดีโอ Reels 9:16 ด้วย FFmpeg...")
    scene_clips = []
    for idx, (img, aud, dur) in enumerate(zip(image_paths, audio_paths, durations), start=1):
        clip_path = VIDEOS_DIR / f"clip_{idx:02d}.mp4"
        print(f"   - กำลังประมวลผลฉากที่ {idx}/{len(scenes)} (ความยาว {dur:.1f}s)...")
        assemble_scene_clip(img, aud, dur, clip_path)
        scene_clips.append(clip_path)

    timestamp_str = time.strftime("%Y%m%d_%H%M%S")
    final_output_file = OUTPUT_DIR / f"reel_{timestamp_str}.mp4"

    final_video = assemble_final_reel(scene_clips, srt_path, final_output_file)

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("🎉 ผลิตวิดีโอเสร็จสมบูรณ์เรียบร้อยแล้ว! (ใช้เวลาเพียง {:.1f} วินาที)".format(elapsed))
    print(f"📁 ที่อยู่วิดีโอ: {final_video.resolve()}")
    print("=" * 60)
    print("📱 สามารถนำคลิปนี้ไปโพสต์ลง TikTok, Instagram Reels, YouTube Shorts ได้ทันที!")

def interactive_mode():
    print("\n==================================================")
    print("✨ ยินดีต้อนรับสู่ AI Reels Video Studio ✨")
    print("==================================================")
    topic = input("👉 ใส่หัวข้อคลิปที่ต้องการ (เช่น เรื่องผีโรงเรียนเก่า, เคล็ดลับดึงดูดเงิน): ").strip()
    if not topic:
        topic = "ตำนานผีไทยสุดเฮี้ยนในป่าช้าเก่า"
        print(f"ใช้หัวข้อตัวอย่าง: {topic}")

    print("\nเลือกสไตล์:")
    print("1. horror (เรื่องสยองขวัญ / ผี / ปริศนาดำมืด)")
    print("2. mystery (คดีลี้ลับ / ประวัติศาสตร์ / สืบสวน)")
    print("3. drama (ดราม่าชีวิต / สตอรี่สอนใจ)")
    print("4. motivation (พัฒนาตนเอง / ปรัชญาความมั่งคั่ง)")
    print("5. history (ประวัติศาสตร์โบราณ)")
    style_choice = input("เลือกสไตล์ (1-5, ค่าเริ่มต้น 1): ").strip()

    style_map = {"1": "horror", "2": "mystery", "3": "drama", "4": "motivation", "5": "history"}
    style = style_map.get(style_choice, "horror")

    print("\nเลือกเสียงพากย์:")
    print("1. ผู้ชาย (th-TH-NiwatNeural - เสียงเข้ม ทรงพลัง)")
    print("2. ผู้หญิง (th-TH-PremwadeeNeural - เสียงใส ชัดเจน)")
    voice_choice = input("เลือกเสียง (1-2, ค่าเริ่มต้น 1): ").strip()
    voice = "female" if voice_choice == "2" else "male"

    run_pipeline(topic=topic, style=style, voice=voice)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Reels Video Studio Generator")
    parser.add_argument("--topic", type=str, help="หัวข้อเนื้อหาของคลิป")
    parser.add_argument("--style", type=str, default="horror", choices=["horror", "mystery", "drama", "motivation", "history"])
    parser.add_argument("--voice", type=str, default="male", choices=["male", "female"])
    parser.add_argument("--scenes", type=int, default=5, help="จำนวนฉาก")
    parser.add_argument("--api-key", type=str, default="", help="Google Gemini API Key")
    parser.add_argument("--preview-only", action="store_true", help="สร้างเฉพาะสคริปต์ ภาพ และเสียง (ไม่เรนเดอร์วิดีโอ)")

    args = parser.parse_args()

    if args.topic:
        run_pipeline(
            topic=args.topic,
            style=args.style,
            voice=args.voice,
            num_scenes=args.scenes,
            preview_only=args.preview_only,
            api_key=args.api_key
        )
    else:
        interactive_mode()
