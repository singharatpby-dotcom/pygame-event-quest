import os
import re
import json
import asyncio
from typing import Optional, List
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Micro-learning AI Assistant API - Pygame Event Handling")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# ⚡ HTTP Client Pool & Concurrency Settings
# ==========================================
# รองรับการเชื่อมต่อพร้อมกัน 20-30 เครื่อง ด้วย Connection Pool
http_limits = httpx.Limits(max_keepalive_connections=50, max_connections=100)
http_timeout = httpx.Timeout(45.0, connect=10.0)

# ==========================================
# 📚 คลังความรู้ 6 บทเรียน (Context Knowledge)
# ==========================================
CONTEXT_KNOWLEDGE = """
ขอบเขตเนื้อหา 6 บทเรียนย่อย (Micro-learning Units) เรื่อง การตรวจจับเหตุการณ์ (Event Handling) ด้วย Pygame:
- บทที่ 1: พื้นฐานและแนวคิดการตรวจจับเหตุการณ์ (Input Events, Window Events, User-defined Events, pygame.init(), pygame.display.set_mode(), pygame.display.set_caption())
- บทที่ 2: โครงสร้างและการจัดการคิวเหตุการณ์ (Game Loop, while running, pygame.event.get() แบบ FIFO, pygame.QUIT, pygame.quit())
- บทที่ 3: การตรวจจับเหตุการณ์จากคีย์บอร์ด (KEYDOWN, KEYUP, event.key เช่น pygame.K_LEFT, pygame.K_RIGHT, pygame.K_SPACE, pygame.key.get_pressed() สำหรับ Continuous actions)
- บทที่ 4: การตรวจจับเหตุการณ์จากเมาส์ (MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, event.button, pygame.mouse.get_pos())
- บทที่ 5: การตรวจจับการชน (Collision Detection, pygame.Rect, colliderect, collidepoint, Sprite collision)
- บทที่ 6: การประยุกต์ใช้ตรรกะเหตุการณ์และการแก้บั๊ก (Game State เช่น PLAYING / PAUSE, Scoring เมื่อเกิดเหตุการณ์, Event Integration & Debugging ด้วย print(event))
"""

# รายละเอียดสำหรับ Code Grader ประจำ 6 บทเรียน
LESSON_DATA = {
    1: {
        "title": "พื้นฐานและแนวคิดการตรวจจับเหตุการณ์",
        "objective": "ตรวจสอบความเข้าใจเรื่องเหตุการณ์ มีการนำเข้าโมดูล pygame, เรียกใช้ pygame.init(), สร้างหน้าต่างด้วย pygame.display.set_mode() และตั้งชื่อหน้าต่างด้วย pygame.display.set_caption()",
        "answer_key": """import pygame

pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("My Pygame Window")
print("Pygame Window Ready!")"""
    },
    2: {
        "title": "โครงสร้างและการจัดการคิวเหตุการณ์",
        "objective": "ตรวจสอบการวนลูป Game Loop (while True หรือ running) และการดักจับ pygame.event.get() พร้อมเงื่อนไขตรวจสอบ event.type == pygame.QUIT เพื่อหยุดการทำงานและเรียก pygame.quit()",
        "answer_key": """import pygame

pygame.init()
screen = pygame.display.set_mode((640, 480))
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()"""
    },
    3: {
        "title": "การตรวจจับเหตุการณ์จากคีย์บอร์ด",
        "objective": "ตรวจสอบการรับค่าจากแป้นพิมพ์ โดยใช้ event.type == pygame.KEYDOWN และเช็คปุ่ม เช่น pygame.K_LEFT, pygame.K_RIGHT หรือ pygame.key.get_pressed()",
        "answer_key": """import pygame

pygame.init()
screen = pygame.display.set_mode((640, 480))
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                print("Move Left")
            elif event.key == pygame.K_RIGHT:
                print("Move Right")

pygame.quit()"""
    },
    4: {
        "title": "การตรวจจับเหตุการณ์จากเมาส์",
        "objective": "ตรวจสอบการรับค่าจากเมาส์ เช่น event.type == pygame.MOUSEBUTTONDOWN หรือ pygame.mouse.get_pos() เพื่อหาพิกัด",
        "answer_key": """import pygame

pygame.init()
screen = pygame.display.set_mode((640, 480))
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            print(f"Mouse clicked at: {pos}")

pygame.quit()"""
    },
    5: {
        "title": "การตรวจจับการชน",
        "objective": "ตรวจสอบการสร้าง Rect หรือ Sprite และการใช้ฟังก์ชันตรวจสอบการชน เช่น rect1.colliderect(rect2)",
        "answer_key": """import pygame

pygame.init()
player_rect = pygame.Rect(100, 100, 50, 50)
coin_rect = pygame.Rect(120, 110, 30, 30)

if player_rect.colliderect(coin_rect):
    print("Collision detected!")
else:
    print("No collision")"""
    },
    6: {
        "title": "การประยุกต์ใช้ตรรกะเหตุการณ์และการแก้บั๊ก",
        "objective": "ตรวจสอบการบูรณาการ เช่น การตรวจจับเหตุการณ์ร่วมกับสถานะเกม (Game State) หรือการตรวจจับเหตุการณ์แล้วคำนวณคะแนน (Scoring)",
        "answer_key": """import pygame

pygame.init()
screen = pygame.display.set_mode((640, 480))
score = 0
state = "PLAYING"
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and state == "PLAYING":
                score += 10
                print(f"Score: {score}")
            elif event.key == pygame.K_ESCAPE:
                state = "PAUSE"
                print("Game Paused")

pygame.quit()"""
    }
}

# ==========================================
# 🛠️ Helper สำหรับเรียก OpenTyphoon AI พร้อม Retry Backoff
# ==========================================
async def call_typhoon_llm(system_prompt: str, user_prompt: str, max_tokens: int = 600, temperature: float = 0.2):
    api_key = os.getenv("API_KEY")
    api_url = "https://api.opentyphoon.ai/v1/chat/completions"

    if not api_key or api_key.startswith("ใส่_"):
        raise HTTPException(status_code=500, detail="กรุณาตั้งค่า API Key ใน Environment Variables ก่อนใช้งาน")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "typhoon-v2.5-30b-a3b-instruct",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    max_retries = 3
    retry_delay = 1.5

    async with httpx.AsyncClient(limits=http_limits, timeout=http_timeout) as client:
        for attempt in range(max_retries):
            try:
                response = await client.post(api_url, json=payload, headers=headers)
                
                # หากติด 429 Too Many Requests ให้หน่วงเวลาและลองใหม่
                if response.status_code == 429 and attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue

                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    if attempt == max_retries - 1:
                        raise HTTPException(status_code=response.status_code, detail=f"AI API Error: {response.text}")
                    await asyncio.sleep(retry_delay)

            except httpx.RequestError as e:
                if attempt == max_retries - 1:
                    raise HTTPException(status_code=500, detail=f"ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ AI ได้: {str(e)}")
                await asyncio.sleep(retry_delay)

# ==========================================
# 1. Endpoint: AI Virtual TA Chatbot
# ==========================================
class ChatRequest(BaseModel):
    message: str
    current_lesson: Optional[int] = None

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    lesson_info = f"นักเรียนกำลังศึกษาบทเรียนที่ {request.current_lesson}" if request.current_lesson else "นักเรียนกำลังเรียนวิชาสร้างเกมคอมพิวเตอร์"
    
    system_prompt = f"""คุณคือ "ครูพี่ผู้ช่วยสอน AI (Virtual TA)" ประจำรายวิชาการสร้างเกมคอมพิวเตอร์ เรื่อง "การตรวจจับเหตุการณ์ (Event Handling) ด้วย Pygame"
ผู้เรียนของคุณคือนักเรียนระดับ ปวช.2 สาขาเทคโนโลยีสารสนเทศ วิทยาลัยเทคนิคพระนครศรีอยุธยา

[บริบทปัจจุบัน]: {lesson_info}

[คลังความรู้ที่ใช้อ้างอิง (Context)]:
{CONTEXT_KNOWLEDGE}

[กฎเหล็กและแนวทางการตอบ (Strict Pedagogical Rules)]:
1. อ้างอิงจากคลังความรู้เท่านั้น: ให้ตอบคำถามโดยอิงจากขอบเขตเนื้อหา 6 บทเรียนข้างต้น หากนักเรียนถามนอกเรื่อง ให้ตอบปฏิเสธอย่างสุภาพและชวนกลับเข้าสู่บทเรียน
2. ห้ามสปอยล์หรือแจกโค้ดสำเร็จรูป (Strictly No Spoon-feeding): 
   - ห้ามเขียนโค้ดคำตอบทั้งชุดให้นักเรียนนำไปก๊อปปี้วางเด็ดขาด
   - ให้นักเรียนได้ฝึกคิดและลงมือทำด้วยตนเอง โดยให้เพียง "คำใบ้ (Hint)", ชี้จุดสังเกต หรือยกตัวอย่างโค้ดแบบ Pseudo-code สั้นๆ 1-2 บรรทัด
3. ป้องกันภาวะข้อมูลล้น (Prevent Cognitive Overload):
   - คำตอบต้อง "สั้น กระชับ ตรงประเด็น" ไม่เกิน 3-5 บรรทัด หรือใช้ Bullet Point สั้นๆ ไม่เกิน 3 ข้อ
   - ใช้ภาษาเข้าใจง่าย ไม่ใช้ศัพท์เทคนิคซับซ้อนเกินระดับ ปวช.
4. การช่วยแก้ข้อผิดพลาด (Debug Assistance):
   - หากนักเรียนส่ง Error หรือโค้ดที่ไม่ทำงานมา ให้บอกจุดที่ผิด (Line/Syntax/Logic) และอธิบายเหตุผลว่าทำไมคอมพิวเตอร์ถึงไม่เข้าใจ พร้อมแนะแนวทางแก้ไข
5. น้ำเสียงและการเสริมแรงเชิงบวก (Gamification & Supportive Tone):
   - ใช้น้ำเสียงเป็นมิตร ให้กำลังใจ เช่น "เกือบถูกแล้วครับ/ค่ะ", "ลองสังเกตตรงจุดนี้ดูนะ", "อีกนิดเดียวจะปลดล็อกเควสต์แล้ว!"
   - ตอบอย่างสุภาพลงท้ายด้วย "ครับ/ค่ะ" เสมอ
"""

    ai_reply = await call_typhoon_llm(
        system_prompt=system_prompt,
        user_prompt=request.message,
        max_tokens=400,
        temperature=0.2
    )

    return {"reply": ai_reply}

# ==========================================
# 2. Endpoint: Automated Code Grader
# ==========================================
class GradeRequest(BaseModel):
    lesson_number: int
    student_code: str

@app.post("/grade-code")
async def grade_code_endpoint(request: GradeRequest):
    lesson_num = request.lesson_number
    lesson = LESSON_DATA.get(lesson_num)
    if not lesson:
        raise HTTPException(status_code=400, detail="ไม่พบบทเรียนที่ระบุ (รองรับบทที่ 1-6)")

    system_prompt = """คุณคือระบบตรวจประเมินผลโค้ดอัตโนมัติ (Automated Code Grader) วิชาการสร้างเกมคอมพิวเตอร์ เรื่อง Pygame Event Handling สำหรับนักเรียน ปวช.2

[เกณฑ์การตรวจประเมิน (Evaluation Rubric)]:
1. ตรรกะสำคัญ (Core Logic): ตรวจสอบว่าโค้ดนักเรียนมีการเรียกใช้ฟังก์ชันหรือตรรกะตามเป้าหมายของบทเรียนหรือไม่ (ไม่จำเป็นต้องเหมือนเฉลยเป๊ะทุกตัวอักษร อนุโลมเรื่องชื่อตัวแปรและการเว้นวรรค)
2. โครงสร้างและการทำงาน (Syntax & Execution Safety): โค้ดต้องไม่มีข้อผิดพลาดทางไวยากรณ์ (Syntax) ที่ทำให้โปรแกรมพัง เช่น ลืม colon (:), การย่อหน้า (Indentation) ผิดเพี้ยน
3. ข้อคิดเห็นป้อนกลับ (Micro-feedback): 
   - หากถูกต้อง: ให้คำชมสั้นๆ และอธิบายว่าทำไมถึงทำได้ดี (กระตุ้นความมั่นใจ)
   - หากไม่ถูกต้อง: ชี้จุดบกพร่องที่ชัดเจน 1-2 จุด และให้คำใบ้โดย "ห้ามเฉลยโค้ดตรงๆ"

[รูปแบบผลลัพธ์ที่ต้องส่งกลับ (บังคับเป็น JSON เท่านั้น)]:
{
  "isCorrect": true หรือ false,
  "scorePercentage": ตัวเลข 0 ถึง 100,
  "summary": "สรุปสั้นๆ ใน 1 บรรทัด",
  "feedback": "คำแนะนำแบบสร้างสรรค์ สั้น กระชับ ตรงประเด็น (ไม่เกิน 3 บรรทัด)",
  "hint": "คำใบ้ชี้จุดให้สังเกตและปรับปรุง (กรณีไม่ผ่าน หากผ่านให้ใส่ null)"
}
คำเตือน: ต้องตอบเป็นรูปแบบ JSON เท่านั้น ห้ามใส่ข้อความอธิบายใดๆ นอก JSON Block"""

    user_prompt = f"""[บริบทบทเรียน]: บทที่ {lesson_num} - {lesson['title']}
[เป้าหมายหลักของบทเรียน]: {lesson['objective']}

[โค้ดเฉลยและเกณฑ์ที่ต้องมี (Answer Key)]:
```python
{lesson['answer_key']}
```

[โค้ดที่นักเรียนส่งมา (Student Code)]:
```python
{request.student_code}
```
"""

    raw_response = await call_typhoon_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=500,
        temperature=0.1
    )

    try:
        json_str = raw_response.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", json_str)
        if match:
            json_str = match.group(1).strip()
        parsed_result = json.loads(json_str)
        return parsed_result
    except Exception:
        return {
            "isCorrect": False,
            "scorePercentage": 50,
            "summary": "ระบบตรวจผลโค้ดเบื้องต้นสำเร็จ",
            "feedback": raw_response[:200],
            "hint": "ลองทบทวนโครงสร้างคำสั่งและเงื่อนไขตามเป้าหมายของบทเรียนดูนะครับ"
        }

# ==========================================
# 3. Endpoint: Quick Error Debugger
# ==========================================
class DebugRequest(BaseModel):
    student_code: str
    error_traceback: str

@app.post("/debug-error")
async def debug_error_endpoint(request: DebugRequest):
    system_prompt = """คุณคือ "AI ผู้ช่วยค้นหาและแก้ไขบัก (Pygame Bug Hunter)" สำหรับนักเรียน ปวช.2

[แนวทางการตอบของ AI]:
1. อธิบายสาเหตุของ Error ด้วยภาษาไทยที่เข้าใจง่ายใน 1-2 บรรทัด (เช่น ลืมใส่เครื่องหมาย, ย่อหน้าไม่เท่ากัน, หรือลืมสร้าง Game Loop)
2. ระบุตำแหน่งบรรทัดที่ทำให้เกิดปัญหาอย่างชัดเจน
3. แนะนำวิธีคิดในการแก้บั๊ก 1 ขั้นตอน (ไม่ให้แจกโค้ดเฉลยทั้งบล็อก แต่ให้ไกด์วิธีแก้เฉพาะจุด)
4. ปิดท้ายด้วยคำให้กำลังใจสไตล์เควสต์เกม เช่น "ลองแก้จุดนี้แล้วกดรันใหม่อีกครั้งนะ นักรบโค้ด! 🚀"

รูปแบบคำตอบ:
- กระชับ ตรงจุด ไม่เกิน 4-5 บรรทัด เพื่อป้องกัน Cognitive Overload
"""

    user_prompt = f"""[ข้อมูลข้อผิดพลาดที่เกิดขึ้น (Error Message / Traceback)]:
{request.error_traceback}

[โค้ดที่มีปัญหาของนักเรียน]:
```python
{request.student_code}
```
"""

    ai_reply = await call_typhoon_llm(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=400,
        temperature=0.2
    )

    return {"debug_advice": ai_reply}

# ==========================================
# 🌐 Static Files Routing (สำหรับ Render.com & ทุกอุปกรณ์)
# ==========================================
@app.get("/")
async def serve_home():
    return FileResponse(BASE_DIR / "Home.html")

@app.get("/Home.html")
async def serve_home_page():
    return FileResponse(BASE_DIR / "Home.html")

@app.get("/Game.html")
async def serve_game_page():
    return FileResponse(BASE_DIR / "Game.html")

@app.get("/Login.html")
async def serve_login_page():
    return FileResponse(BASE_DIR / "Login.html")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Pygame Event Quest",
        "ready": True
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
