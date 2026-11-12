import os
import io
from pathlib import Path
from PIL import Image, ImageDraw
from config import GEMINI_API_KEY, VIDEO_WIDTH, VIDEO_HEIGHT

def generate_image_google_imagen(
    prompt: str,
    output_path: Path,
    api_key: str = None
) -> Path:
    """
    สร้างภาพแนวตั้ง 9:16 ด้วย Google Imagen 3 (imagen-3.0-generate-002)
    เชื่อมต่อโดยตรงผ่าน Google Gemini API Key
    """
    if not api_key:
        api_key = GEMINI_API_KEY

    if not api_key:
        raise ValueError("ไม่พบ GEMINI_API_KEY")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    # ปรับแต่ง Prompt ให้เหมาะกับ Imagen 3 สไตล์ Cinematic Reel
    enhanced_prompt = f"{prompt}, vertical composition, 9:16 aspect ratio, dramatic cinematic lighting, photorealistic, 8k resolution, masterpiece"

    result = client.models.generate_images(
        model="imagen-3.0-generate-002",
        prompt=enhanced_prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="9:16",
            output_mime_type="image/jpeg",
        )
    )

    if result.generated_images:
        image_bytes = result.generated_images[0].image.image_bytes
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        return output_path
    else:
        raise RuntimeError("Google Imagen 3 ไม่ได้ส่งข้อมูลภาพกลับมา")

def create_fallback_image(prompt: str, output_path: Path, width: int = VIDEO_WIDTH, height: int = VIDEO_HEIGHT) -> Path:
    """
    สร้างภาพบรรยากาศ Cinematic สำรอง หากยังไม่ได้เปิดใช้งาน Imagen API
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (width, height), color=(12, 14, 20))
    draw = ImageDraw.Draw(img)

    # วาด Gradient ให้มีมิติ Dark Cinematic
    for y in range(height):
        ratio = y / height
        r = int(10 + 20 * ratio)
        g = int(8 + 15 * ratio)
        b = int(22 + 35 * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # ตกแต่งแถบแสง
    draw.ellipse([width//4, height//3, width*3//4, height*2//3], outline=(60, 50, 100), width=3)

    # ข้อความประกอบฉาก
    clean_p = prompt[:160] + "..." if len(prompt) > 160 else prompt
    draw.text((100, height // 2 - 80), f"Cinematic Scene\n\n{clean_p}", fill=(220, 220, 240))

    img.save(output_path, "JPEG", quality=95)
    return output_path

def generate_scene_images(scenes: list, output_dir: Path, api_key: str = None) -> list:
    """
    สร้างภาพสำหรับทุกฉากในโปรเจกต์
    """
    image_paths = []
    for scene in scenes:
        scene_id = scene.get("scene_id", 1)
        prompt = scene.get("visual_prompt", "cinematic dramatic atmosphere")
        out_file = output_dir / f"scene_{scene_id:02d}.jpg"

        print(f"🎨 [Image AI] กำลังสร้างภาพฉากที่ {scene_id} ด้วย Google Imagen 3...")
        try:
            res_path = generate_image_google_imagen(prompt, out_file, api_key)
            print(f"   ✓ ฉากที่ {scene_id} สร้างสำเร็จด้วย Imagen 3")
        except Exception as e:
            print(f"   ⚠️ Imagen 3 ({e}) กำลังใช้ภาพ Cinematic สำรอง...")
            res_path = create_fallback_image(prompt, out_file)

        image_paths.append(res_path)

    return image_paths
