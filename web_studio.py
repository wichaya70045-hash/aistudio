import os
import sys
import json
import time
import threading
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

sys.path.insert(0, str(Path(__file__).resolve().parent))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config import (
    OUTPUT_DIR,
    AUDIO_DIR,
    IMAGES_DIR,
    VIDEOS_DIR,
    GEMINI_API_KEY,
    VOICE_PRESETS
)
from pipeline.script_gen import generate_reel_script
from pipeline.voice_gen import generate_scene_voices
from pipeline.image_gen import generate_scene_images
from pipeline.assembler import assemble_scene_clip, assemble_final_reel

HOST = "0.0.0.0"
PORT = 8080

CURRENT_STATUS = {
    "status": "idle",
    "step": 0,
    "total_steps": 4,
    "message": "พร้อมสร้างคลิปใหม่",
    "video_url": None,
    "script": None
}

def run_background_generation(topic, style, voice, num_scenes, user_api_key=""):
    global CURRENT_STATUS
    CURRENT_STATUS["status"] = "processing"
    CURRENT_STATUS["video_url"] = None
    CURRENT_STATUS["script"] = None

    active_api_key = user_api_key.strip() if user_api_key and user_api_key.strip() else GEMINI_API_KEY

    if not active_api_key:
        CURRENT_STATUS["status"] = "error"
        CURRENT_STATUS["message"] = "ไม่พบ Gemini API Key! กรุณากรอก API Key ของคุณในช่องด้านบน หรือตั้งค่าใน .env"
        return

    try:
        # Step 1
        CURRENT_STATUS["step"] = 1
        CURRENT_STATUS["message"] = "กำลังเขียนบทและสตอรี่บอร์ดด้วย Gemini AI..."
        script_data = generate_reel_script(
            topic=topic,
            style=style,
            num_scenes=num_scenes,
            api_key=active_api_key
        )
        CURRENT_STATUS["script"] = script_data

        scenes = script_data.get("scenes", [])

        # Step 2
        CURRENT_STATUS["step"] = 2
        CURRENT_STATUS["message"] = f"กำลังสร้างเสียงพากย์ ({voice}) และซับไตเติล..."
        audio_paths, durations, srt_path = generate_scene_voices(
            scenes=scenes,
            output_dir=AUDIO_DIR,
            voice_type=voice
        )

        # Step 3
        CURRENT_STATUS["step"] = 3
        CURRENT_STATUS["message"] = f"กำลังสร้างภาพ AI แนวตั้ง 9:16 ด้วย Google Imagen 3 ({len(scenes)} ภาพ)..."
        image_paths = generate_scene_images(
            scenes=scenes,
            output_dir=IMAGES_DIR,
            api_key=active_api_key
        )

        # Step 4
        CURRENT_STATUS["step"] = 4
        CURRENT_STATUS["message"] = "กำลังตัดต่อและเรนเดอร์วิดีโอ 9:16 ด้วย FFmpeg..."
        scene_clips = []
        for idx, (img, aud, dur) in enumerate(zip(image_paths, audio_paths, durations), start=1):
            clip_path = VIDEOS_DIR / f"clip_{idx:02d}.mp4"
            assemble_scene_clip(img, aud, dur, clip_path)
            scene_clips.append(clip_path)

        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        final_video_name = f"reel_{timestamp_str}.mp4"
        final_output_file = OUTPUT_DIR / final_video_name

        assemble_final_reel(scene_clips, srt_path, final_output_file)

        CURRENT_STATUS["status"] = "completed"
        CURRENT_STATUS["message"] = "สร้างวิดีโอสำเร็จเรียบร้อยแล้ว!"
        CURRENT_STATUS["video_url"] = f"/output/{final_video_name}"

    except Exception as e:
        CURRENT_STATUS["status"] = "error"
        CURRENT_STATUS["message"] = f"เกิดข้อผิดพลาด: {str(e)}"

HTML_PAGE = """<!DOCTYPE html>
<html lang="th" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Reels Studio - เครื่องมือสร้างคลิปแนวตั้งอัตโนมัติ</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Kanit', sans-serif; }
    .glow { box-shadow: 0 0 25px -5px rgba(99, 102, 241, 0.4); }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen">
  <header class="border-b border-slate-800 bg-slate-900/50 backdrop-blur sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <span class="text-3xl">🎬</span>
        <div>
          <h1 class="text-xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            AI Reels Video Studio
          </h1>
          <p class="text-xs text-slate-400">สร้างคลิปสั้นแนวตั้ง 9:16 ด้วย AI อัตโนมัติในคลิกเดียว</p>
        </div>
      </div>
      <div class="flex items-center space-x-3">
        <span id="keyStatusBadge" class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700">
          🔑 เช็คสถานะ Key...
        </span>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
    <!-- Left Column: Settings -->
    <div class="lg:col-span-5 space-y-6">
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 glow">
        <h2 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <span>⚙️</span> ตั้งค่าคลิป & API Key
        </h2>

        <!-- Gemini API Key Input (Customizable per user) -->
        <div class="bg-slate-800/60 border border-slate-700/80 rounded-xl p-3.5 mb-5 space-y-2">
          <div class="flex items-center justify-between">
            <label class="text-xs font-semibold text-indigo-300 flex items-center gap-1.5">
              <span>🔑</span> Google Gemini API Key
            </label>
            <a href="https://aistudio.google.com/" target="_blank" class="text-[11px] text-indigo-400 hover:underline">
              รับฟรีที่นี่ ↗
            </a>
          </div>
          <div class="relative">
            <input 
              id="apiKeyInput" 
              type="password" 
              class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 pr-10 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500" 
              placeholder="AIzaSy... (เว้นว่างไว้เพื่อใช้ Key ของเซิร์ฟเวอร์)"
              oninput="handleApiKeyChange(this.value)"
            />
            <button 
              type="button" 
              onclick="toggleApiKeyVisibility()" 
              class="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 text-xs"
              title="แสดง/ซ่อน Key"
            >
              👁️
            </button>
          </div>
          <p class="text-[11px] text-slate-400 leading-relaxed">
            💡 <strong>สำหรับผู้ใช้คนอื่น:</strong> สามารถใส่ Key ของตัวเองได้ ระบบจะบันทึกไว้ใน Browser ของคุณเท่านั้น ปลอดภัย ไม่ปนกับคนอื่น
          </p>
        </div>

        <!-- Topic Input -->
        <div class="space-y-2 mb-4">
          <label class="block text-sm font-medium text-slate-300">หัวข้อเรื่องที่ต้องการสร้าง</label>
          <textarea id="topicInput" rows="3" class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500" placeholder="เช่น ตำนานผีไทยสุดเฮี้ยนในป่าช้าเก่า, จิตวิทยาความลับของคนรวย 1%..."></textarea>
        </div>

        <!-- Quick Presets -->
        <div class="mb-5">
          <span class="text-xs text-slate-400 block mb-2">⚡ หัวข้อยอดนิยม (คลิกเพื่อเลือก):</span>
          <div class="flex flex-wrap gap-2">
            <button onclick="setTopic('ตำนานเรื่องผีในโรงพยาบาลร้าง', 'horror')" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-xs rounded-lg text-slate-300 border border-slate-700">👻 เรื่องผีรพ.ร้าง</button>
            <button onclick="setTopic('3 กฎจิตวิทยาที่ทำให้คนเกรงใจคุณ', 'motivation')" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-xs rounded-lg text-slate-300 border border-slate-700">🧠 จิตวิทยาสะกดใจ</button>
            <button onclick="setTopic('ความลับของปิรามิดที่นักวิทย์ยังหาคำตอบไม่ได้', 'mystery')" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-xs rounded-lg text-slate-300 border border-slate-700">🔍 ปริศนาปิรามิด</button>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4 mb-5">
          <!-- Style -->
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-1">สไตล์คลิป</label>
            <select id="styleSelect" class="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500">
              <option value="horror">👻 Horror (สยองขวัญ/ผี)</option>
              <option value="mystery">🔍 Mystery (ลี้ลับ/สืบสวน)</option>
              <option value="drama">🎭 Drama (ดราม่าสอนใจ)</option>
              <option value="motivation">💎 Motivation (พัฒนาตนเอง)</option>
              <option value="history">🏛️ History (ประวัติศาสตร์)</option>
            </select>
          </div>

          <!-- Voice -->
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-1">เสียงพากย์</label>
            <select id="voiceSelect" class="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500">
              <option value="male">👨 ชาย (นิวัฒน์ - เสียงเข้ม/มีพลัง)</option>
              <option value="female">👩 หญิง (เปรมวดี - เสียงใส/นุ่ม)</option>
            </select>
          </div>
        </div>

        <!-- Scenes Count -->
        <div class="mb-6">
          <div class="flex justify-between text-sm mb-1">
            <span class="text-slate-300">จำนวนฉาก:</span>
            <span id="sceneCountLabel" class="text-indigo-400 font-semibold">5 ฉาก (~45-60s)</span>
          </div>
          <input id="scenesInput" type="range" min="3" max="8" value="5" class="w-full accent-indigo-500" oninput="updateSceneLabel(this.value)">
        </div>

        <!-- Submit Button -->
        <button id="generateBtn" onclick="startGeneration()" class="w-full py-4 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-bold rounded-xl shadow-lg transition-all flex items-center justify-center gap-2">
          <span id="btnIcon">🚀</span> <span id="btnText">เริ่มสร้างวิดีโอ Reels 9:16</span>
        </button>
      </div>

      <!-- Live Status -->
      <div id="statusCard" class="bg-slate-900 border border-slate-800 rounded-2xl p-5 hidden">
        <h3 class="text-sm font-semibold text-slate-300 mb-3 flex items-center justify-between">
          <span>ความคืบหน้าการผลิต</span>
          <span id="stepBadge" class="text-xs bg-indigo-500/20 text-indigo-400 px-2 py-0.5 rounded">0/4</span>
        </h3>
        <p id="statusMsg" class="text-sm text-slate-300 mb-3 animate-pulse">กำลังประมวลผล...</p>
        <div class="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
          <div id="progressBar" class="bg-indigo-500 h-2 transition-all duration-300" style="width: 0%"></div>
        </div>
      </div>
    </div>

    <!-- Right Column: Video & Storyboard Preview -->
    <div class="lg:col-span-7 space-y-6">
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col items-center justify-center min-h-[580px]">
        <div id="placeholderView" class="text-center p-8">
          <div class="w-20 h-20 mx-auto mb-4 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-4xl">
            📱
          </div>
          <h3 class="text-lg font-semibold text-slate-200 mb-1">ยังไม่มีวิดีโอที่กำลังเล่น</h3>
          <p class="text-sm text-slate-400 max-w-sm">
            กรอกหัวข้อที่ต้องการทางด้านซ้าย แล้วกด "เริ่มสร้างวิดีโอ" ระบบ AI จะแต่งบท เจนภาพ พากย์เสียง และตัดต่อให้อัตโนมัติ
          </p>
        </div>

        <!-- Video Player View (Initially hidden) -->
        <div id="videoContainer" class="hidden flex flex-col items-center w-full">
          <h3 id="videoTitle" class="text-base font-bold text-slate-100 mb-3 text-center"></h3>
          <div class="relative rounded-2xl overflow-hidden border-2 border-indigo-500/50 shadow-2xl bg-black max-w-[340px] w-full aspect-[9/16]">
            <video id="reelPlayer" controls class="w-full h-full object-cover">
              <source id="videoSource" src="" type="video/mp4">
            </video>
          </div>
          <a id="downloadBtn" href="" download class="mt-4 px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm rounded-xl flex items-center gap-2 transition">
            <span>⬇️</span> ดาวน์โหลดคลิป MP4 พร้อมโพสต์
          </a>
        </div>
      </div>
    </div>
  </main>

  <script>
    // Load saved API Key from localStorage
    window.addEventListener('DOMContentLoaded', () => {
      const savedKey = localStorage.getItem('user_gemini_api_key') || '';
      if (savedKey) {
        document.getElementById('apiKeyInput').value = savedKey;
      }
      updateKeyBadge(savedKey);
    });

    function handleApiKeyChange(val) {
      localStorage.setItem('user_gemini_api_key', val.trim());
      updateKeyBadge(val.trim());
    }

    function updateKeyBadge(val) {
      const badge = document.getElementById('keyStatusBadge');
      if (val) {
        badge.className = "inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
        badge.innerHTML = "● ใช้ Custom Key";
      } else {
        badge.className = "inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700";
        badge.innerHTML = "● ใช้ Server Key (.env)";
      }
    }

    function toggleApiKeyVisibility() {
      const input = document.getElementById('apiKeyInput');
      input.type = input.type === 'password' ? 'text' : 'password';
    }

    function setTopic(text, style) {
      document.getElementById('topicInput').value = text;
      document.getElementById('styleSelect').value = style;
    }

    function updateSceneLabel(val) {
      document.getElementById('sceneCountLabel').innerText = `${val} ฉาก (~${val * 10 - 5}-${val * 12}s)`;
    }

    let pollInterval = null;

    async function startGeneration() {
      const topic = document.getElementById('topicInput').value.trim();
      if (!topic) {
        alert('กรุณากรอกหัวข้อที่ต้องการสร้างก่อนครับ');
        return;
      }

      const apiKey = document.getElementById('apiKeyInput').value.trim();
      const style = document.getElementById('styleSelect').value;
      const voice = document.getElementById('voiceSelect').value;
      const scenes = parseInt(document.getElementById('scenesInput').value);

      document.getElementById('generateBtn').disabled = true;
      document.getElementById('generateBtn').classList.add('opacity-50', 'cursor-not-allowed');
      document.getElementById('statusCard').classList.remove('hidden');

      try {
        const resp = await fetch('/api/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            topic, 
            style, 
            voice, 
            num_scenes: scenes,
            api_key: apiKey
          })
        });
        const data = await resp.json();
        
        if (data.status === 'started') {
          pollInterval = setInterval(checkStatus, 2000);
        } else if (data.error) {
          alert('ข้อผิดพลาด: ' + data.error);
          resetButton();
        }
      } catch (e) {
        alert('เชื่อมต่อเซิร์ฟเวอร์ล้มเหลว: ' + e);
        resetButton();
      }
    }

    async function checkStatus() {
      try {
        const resp = await fetch('/api/status');
        const data = await resp.json();

        document.getElementById('statusMsg').innerText = data.message;
        const progress = Math.min(100, Math.round((data.step / 4) * 100));
        document.getElementById('progressBar').style.width = progress + '%';
        document.getElementById('stepBadge').innerText = `${data.step}/4`;

        if (data.status === 'completed') {
          clearInterval(pollInterval);
          resetButton();
          showVideo(data.video_url, data.script?.title || 'Reel Video');
        } else if (data.status === 'error') {
          clearInterval(pollInterval);
          resetButton();
          alert('เกิดข้อผิดพลาด: ' + data.message);
        }
      } catch (e) {
        console.error(e);
      }
    }

    function showVideo(url, title) {
      document.getElementById('placeholderView').classList.add('hidden');
      document.getElementById('videoContainer').classList.remove('hidden');
      document.getElementById('videoTitle').innerText = title;
      const player = document.getElementById('reelPlayer');
      const source = document.getElementById('videoSource');
      source.src = url;
      player.load();
      document.getElementById('downloadBtn').href = url;
    }

    function resetButton() {
      document.getElementById('generateBtn').disabled = false;
      document.getElementById('generateBtn').classList.remove('opacity-50', 'cursor-not-allowed');
    }
  </script>
</body>
</html>
"""

class StudioRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif parsed.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(CURRENT_STATUS, ensure_ascii=False).encode("utf-8"))
        elif parsed.path.startswith("/output/"):
            rel_path = parsed.path.replace("/output/", "", 1)
            file_path = OUTPUT_DIR / rel_path
            if file_path.exists() and file_path.is_file():
                self.send_response(200)
                if file_path.suffix == ".mp4":
                    self.send_header("Content-Type", "video/mp4")
                elif file_path.suffix in [".jpg", ".jpeg"]:
                    self.send_header("Content-Type", "image/jpeg")
                elif file_path.suffix == ".mp3":
                    self.send_header("Content-Type", "audio/mpeg")
                else:
                    self.send_header("Content-Type", "application/octet-stream")
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "File Not Found")
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == "/api/generate":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            params = json.loads(body.decode("utf-8"))

            topic = params.get("topic", "ตำนานเรื่องผี")
            style = params.get("style", "horror")
            voice = params.get("voice", "male")
            num_scenes = int(params.get("num_scenes", 5))
            user_api_key = params.get("api_key", "").strip()

            # Run in separate thread
            t = threading.Thread(
                target=run_background_generation,
                args=(topic, style, voice, num_scenes, user_api_key),
                daemon=True
            )
            t.start()

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "started"}).encode("utf-8"))
        else:
            self.send_error(404, "Not Found")

def start_server():
    server = HTTPServer((HOST, PORT), StudioRequestHandler)
    print("=" * 60)
    print("✨ AI REELS STUDIO WEB APP IS READY! ✨")
    print(f"🌐 เข้าใช้งานผ่านเครื่องนี้:   http://localhost:{PORT}")
    print(f"🌐 ให้คนอื่นในวง LAN ใช้:    http://<YOUR_IP>:{PORT}")
    print("=" * 60)
    server.serve_forever()

# Export for Vercel / Serverless function runtime
handler = StudioRequestHandler
app = StudioRequestHandler

if __name__ == "__main__":
    start_server()
