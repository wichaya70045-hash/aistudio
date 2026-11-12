# 🎬 AI Reels Video Studio

สตูดิโอสร้างคลิปวิดีโอสั้นแนวตั้ง (9:16) อัตโนมัติสำหรับ **TikTok, Instagram Reels, YouTube Shorts** เพื่อสร้างรายได้ (Ad Revenue & Sponsorship) ด้วยต้นทุนต่ำที่สุด

---

## 🌟 ฟีเจอร์เด่น (Key Features)

- 🧠 **AI Scriptwriter (Gemini 2.0 Flash):** แต่งบทแบบ Viral Formula มี Hook เปิดเรื่อง 3 วินาทีแรก แบ่งฉาก 4-6 ฉาก พร้อมคำบรรยายภาษาไทย และ Visual Prompts ภาษาอังกฤษ
- 🎙️ **Natural Thai Voiceover (Edge-TTS):** พากย์เสียงภาษาไทยระดับสตูดิโอฟรี 100% ไม่ต้องใช้ API Key
  - `th-TH-NiwatNeural` (ชาย เสียงเข้ม ทรงพลัง เหมาะกับเรื่องเล่า/เรื่องผี/ประวัติศาสตร์)
  - `th-TH-PremwadeeNeural` (หญิง เสียงนุ่มนวล ชัดเจน เหมาะกับดราม่า/ข้อคิด)
- 🎨 **AI Image Generation (Flux.1 / SDXL):** เจนภาพแนวตั้ง 1080x1920 สไตล์ Cinematic ฟรีผ่าน Pollinations Engine
- 🎞️ **FFmpeg Video Assembler:** รวมภาพและเสียงเข้าด้วยกัน พร้อมเอฟเฟกต์ Ken Burns (Zoom ช้าๆ) ให้ภาพดูมีชีวิตชีวา
- 📝 **Auto Thai Subtitles:** ฝังซับไตเติลภาษาไทยสีขาว ขอบดำหนา อ่านง่าย ชัดเจน ตรงตามสไตล์ Reels/Shorts
- 🌐 **Built-in Web Studio:** มีหน้าเว็บ UI ให้ใช้งานผ่าน Browser ได้ทันที
- 👥 **Multi-User Friendly:** มีช่องให้ผู้ใช้งานแต่ละคนใส่ Google Gemini API Key ของตนเองบนหน้าเว็บได้ทันที (ระบบจำไว้ใน Browser ของแต่ละคน ไม่ต้องแก้ไฟล์เซิร์ฟเวอร์)

---

## 🚀 เริ่มต้นใช้งานใน 3 นาที

### 1. ใส่ Gemini API Key ในไฟล์ `.env`
เปิดไฟล์ `.env` ในโฟลเดอร์นี้ แล้ววาง API Key ที่ได้ฟรีจาก [Google AI Studio](https://aistudio.google.com/):

```env
GEMINI_API_KEY=วาง_API_KEY_ของคุณที่นี่
```

### 2. วิธีใช้งาน (เลือกได้ 2 รูปแบบ)

#### รูปแบบที่ 1: ผ่านหน้าเว็บ Web Studio (แนะนำ ใช้งานง่ายที่สุด)
รันคำสั่ง:
```bash
python web_studio.py
```
จากนั้นเปิดเบราว์เซอร์ไปที่: **`http://localhost:8080`**
- กรอกหัวข้อ หรือเลือกจาก Quick Presets
- เลือกสไตล์ (Horror, Mystery, Drama, Motivation, History)
- กด **"เริ่มสร้างวิดีโอ"** แล้วรอดูวิดีโอบนหน้าจอพร้อมปุ่มดาวน์โหลดได้เลย!

#### รูปแบบที่ 2: ผ่าน Command Line (CLI)
สร้างแบบ Interactive (มีเมนูให้เลือก):
```bash
python main.py
```

หรือสร้างแบบระบุคำสั่งเดียว (One-Liner):
```bash
# ตัวอย่าง: สร้างเรื่องผี
python main.py --topic "ตำนานผีตายทั้งกลมในป่าช้าเก่า" --style horror --voice male

# ตัวอย่าง: สร้างจิตวิทยาความสำเร็จ
python main.py --topic "3 นิสัยของคนที่ประสบความสำเร็จอย่างเงียบๆ" --style motivation --voice female
```

---

## 📂 โครงสร้างโปรเจกต์

```
videostudeo/
├── 📄 config.py              # การตั้งค่าระบบ, พาธ FFmpeg และโฟลเดอร์
├── 📄 main.py                # ระบบรันผ่าน CLI
├── 📄 web_studio.py          # เซิร์ฟเวอร์ Web Studio (UI สวยงาม พร้อมเล่นวิดีโอ)
├── 📄 requirements.txt       # รายชื่อแพ็กเกจที่จำเป็น
├── 📄 .env                   # เก็บ API Key
├── 📁 pipeline/
│   ├── 📄 script_gen.py      # โมดูลเขียนบท (Gemini 2.0 Flash)
│   ├── 📄 voice_gen.py       # โมดูลสร้างเสียงพากย์ + Subtitle SRT (Edge-TTS)
│   ├── 📄 image_gen.py       # โมดูลเจนภาพ 9:16 (Flux Engine)
│   └── 📄 assembler.py       # โมดูลตัดต่อวิดีโอและฝังซับไตเติล (FFmpeg)
└── 📁 output/
    ├── 📁 audio/             # ไฟล์เสียงพากย์ของแต่ละฉาก (.mp3)
    ├── 📁 images/            # ภาพ AI แนวตั้งของแต่ละฉาก (.jpg)
    ├── 📁 videos/            # วิดีโอแต่ละฉาก (.mp4)
    └── 🎬 reel_*.mp4         # วิดีโอคลิปฉบับเต็มพร้อมนำไปโพสต์
```

---

## 💰 กลยุทธ์การทำเงินจากคลิปสั้น
1. **โพสต์สม่ำเสมอ:** วันละ 2-3 คลิป ในเวลาคนเล่นเยอะ (11:00-13:00 น. หรือ 19:00-22:00 น.)
2. **โพสต์ข้ามแพลตฟอร์ม:** คลิปเดียวกันลงทั้ง **TikTok, Instagram Reels, YouTube Shorts และ Facebook Reels**
3. **ติดแฮชแท็กที่ตรงกลุ่มเป้าหมาย:** เช่น `#เรื่องผี #เรื่องหลอน #สปอยหนัง #ข้อคิดดีๆ`
