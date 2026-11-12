import os
import json
import re
from typing import Dict, Any
from google import genai
from google.genai import types

STYLE_GUIDELINES = {
    "horror": (
        "แนวเรื่องสยองขวัญ / เรื่องผีไทย / ตำนานลี้ลับ บรรยากาศมืดมน หลอน น่ากลัว "
        "ภาพแนว dark cinematic, foggy, eerie lighting, haunted atmosphere, 8k resolution"
    ),
    "mystery": (
        "แนวสืบสวน / ความลึกลับทางประวัติศาสตร์ / คดีปริศนา บรรยากาศน่าค้นหา ลุ้นระทึก "
        "ภาพแนว vintage documentary, mysterious shadows, dramatic lighting, cinematic film grain"
    ),
    "drama": (
        "แนวดราม่าชีวิต / บทเรียนความรัก / หักมุมสะเทือนอารมณ์ สไตล์ ReelShort "
        "ภาพแนว modern cinematic drama, expressive characters, shallow depth of field, emotional lighting"
    ),
    "motivation": (
        "แนวสร้างแรงบันดาลใจ / ปรัชญาชีวิต / จิตวิทยาความสำเร็จ สไตล์ Stoic หรือ Luxury "
        "ภาพแนว luxury aesthetic, golden hour, epic scale, moody cinematic, high contrast"
    ),
    "history": (
        "แนวประวัติศาสตร์โบราณ / วีรบุรุษ / อารยธรรมที่สาบสูญ "
        "ภาพแนว historical epic, ancient architectural details, atmospheric lighting, hyperrealistic"
    ),
}

def generate_reel_script(
    topic: str,
    style: str = "horror",
    num_scenes: int = 5,
    api_key: str = None
) -> Dict[str, Any]:
    """
    สร้างบท Reels 9:16 (Hook, เนื้อเรื่องแบ่งฉาก, Prompt ภาพ, คำบรรยายภาษาไทย)
    """
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY", "")

    if not api_key:
        raise ValueError("ไม่พบ GEMINI_API_KEY กรุณากำหนดในไฟล์ .env หรือส่งผ่านพารามิเตอร์")

    client = genai.Client(api_key=api_key)
    style_info = STYLE_GUIDELINES.get(style, STYLE_GUIDELINES["horror"])

    system_instruction = (
        "คุณคือสุดยอดนักเขียนบทคลิปสั้น Viral ระดับโลกสำหรับ TikTok, Instagram Reels และ YouTube Shorts\n"
        "กฎเหล็ก:\n"
        "1. Hook (ประโยคเปิด 3 วินาทีแรก) ต้องหยุดนิ้วคนดูทันที ดึงดูด กระตุ้นความอยากรู้ หรือน่าตกใจ\n"
        "2. คำบรรยาย (narration) ต้องเป็นภาษาไทยธรรมชาติ มีจังหวะวรรคตอนที่เหมาะกับการพากย์เสียง\n"
        "3. visual_prompt ต้องเป็นภาษาอังกฤษที่ละเอียด คมชัด สไตล์ Cinematic และระบุว่า vertical 9:16 composition\n"
        "4. ตอบกลับเป็น JSON ที่ถูกต้องตาม Schema เท่านั้น ห้ามมีข้อความอื่นปน"
    )

    prompt = f"""
สร้างสคริปต์คลิปสั้นแนวตั้ง (Vertical Reel) ความยาวรวมประมาณ 45-60 วินาที
หัวข้อ: "{topic}"
สไตล์: "{style}" ({style_info})
จำนวนฉาก: {num_scenes} ฉาก

โครงสร้าง JSON ที่ต้องการ:
{{
  "title": "ชื่อคลิปภาษาไทยที่น่ากดดูสุดๆ (Clickbait แต่ตรงประเด็น)",
  "hook": "ประโยคเปิด 1-2 ประโยคสำหรับฉากแรก (สะกดคนดูทันที)",
  "category": "{style}",
  "scenes": [
    {{
      "scene_id": 1,
      "narration": "ข้อความภาษาไทยสำหรับพากย์เสียงในฉากนี้ (ความยาว 15-25 คำ)",
      "visual_prompt": "Ultra-detailed English prompt for AI image generator, vertical 9:16 aspect ratio, cinematic lighting, photorealistic, 8k",
      "camera_motion": "slow zoom in"
    }}
  ],
  "cta": "คำกระตุ้นท้ายคลิปภาษาไทย (เช่น คอมเมนต์บอกเรา หรือกดติดตามเพื่อดูต่อ)",
  "hashtags": ["#เรื่องผี", "#เรื่องสยองขวัญ", "#reels"]
}}
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            temperature=0.8,
        ),
    )

    raw_text = response.text.strip()
    # Clean json markdown tags if any
    raw_text = re.sub(r"^```json\s*", "", raw_text)
    raw_text = re.sub(r"\s*```$", "", raw_text)

    data = json.loads(raw_text)
    return data
