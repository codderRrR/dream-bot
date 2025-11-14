from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import sqlite3
import os
from datetime import datetime
from gigachat_api import gigachat
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from vk_bot import VKBot
from dotenv import load_dotenv
import uvicorn

load_dotenv()

app = FastAPI(title="ИИ Сонник", description="Психологическая интерпретация снов")

# Монтируем статические файлы
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
    print("✅ Статические файлы подключены")
else:
    print("⚠️ Папка static не найдена")

# Инициализация VK бота
VK_GROUP_TOKEN = os.getenv("VK_GROUP_TOKEN")
if VK_GROUP_TOKEN:
    vk_bot = VKBot(VK_GROUP_TOKEN)
    print("✅ VK Bot инициализирован")
else:
    vk_bot = None
    print("⚠️ VK_GROUP_TOKEN не найден")

# 🔥 КОНСТАНТЫ VK
CONFIRMATION_TOKEN = "6da970f6"

# 🔥 ПРОСТОЙ WEBHOOK ДЛЯ БЫСТРОГО ТЕСТА
@app.get("/vk_simple")
async def vk_simple_webhook(user_id: int, text: str = "привет"):
    """Простой webhook через GET для тестирования"""
    if vk_bot is None:
        return {"error": "VK bot not initialized"}
    
    print(f"🔧 Simple webhook: user_id={user_id}, text='{text}'")
    
    response_text = vk_bot.handle_message(user_id, text)
    sent = vk_bot.send_message(user_id, response_text)
    
    return {
        "status": "success" if sent else "error",
        "user_id": user_id,
        "original_text": text,
        "response": response_text,
        "sent": sent
    }

# 🔥 ТЕСТОВЫЙ ЭНДПОИНТ ДЛЯ РУЧНОЙ ОТПРАВКИ
@app.get("/send_vk")
async def send_vk_message(user_id: int, message: str = "тест"):
    """Ручная отправка сообщения в VK"""
    if vk_bot is None:
        return {"status": "error", "message": "VK bot not initialized"}
    
    print(f"🔧 Ручная отправка: user_id={user_id}, message='{message}'")
    sent = vk_bot.send_message(user_id, message)
    
    return {
        "status": "success" if sent else "error",
        "user_id": user_id,
        "message": message,
        "sent": sent
    }

# 🔥 ТЕСТ VK БОТА
@app.get("/test_vk")
async def test_vk(user_id: int, message: str = "привет"):
    """Тестирование VK бота"""
    if vk_bot is None:
        return {"status": "error", "message": "VK bot not initialized"}
    
    print(f"🔧 Тест VK: user_id={user_id}, message='{message}'")
    
    response_text = vk_bot.handle_message(user_id, message)
    print(f"🔧 Ответ бота: '{response_text}'")
    
    keyboard = vk_bot.get_default_keyboard()
    sent = vk_bot.send_message(user_id, response_text, keyboard)
    
    return {
        "status": "success",
        "user_id": user_id,
        "response": response_text,
        "sent": sent,
        "message": "Проверьте сообщения в VK!"
    }

# 🔥 ИСПРАВЛЕННЫЙ CALLBACK ДЛЯ VK
@app.api_route("/vk_callback", methods=["GET", "POST"])
async def vk_callback(request: Request):
    """Callback API для VK"""
    print(f"🔥 VK CALLBACK: {request.method}")
    
    # GET запрос - подтверждение сервера
    if request.method == "GET":
        params = dict(request.query_params)
        print(f"🔥 GET PARAMS: {params}")
        
        if params.get("type") == "confirmation":
            print(f"🔥 RETURNING CONFIRMATION: {CONFIRMATION_TOKEN}")
            return Response(content=CONFIRMATION_TOKEN, media_type="text/plain")
        
        return Response(content="ok", media_type="text/plain")
    
    # POST запрос - обработка событий
    try:
        data = await request.json()
        print(f"🔥 POST DATA: {data}")
        
        if data.get("type") == "confirmation":
            print(f"🔥 CONFIRMATION IN POST: {CONFIRMATION_TOKEN}")
            return Response(content=CONFIRMATION_TOKEN, media_type="text/plain")
        
        # Новое сообщение
        elif data.get("type") == "message_new":
            message_data = data["object"]["message"]
            user_id = message_data["from_id"]
            text = message_data["text"]
            
            print(f"🔧 Новое сообщение VK от {user_id}: '{text}'")
            
            if vk_bot:
                response_text = vk_bot.handle_message(user_id, text)
                keyboard = vk_bot.get_default_keyboard()
                sent = vk_bot.send_message(user_id, response_text, keyboard)
                print(f"🔧 Ответ отправлен в VK: {sent}")
        
        return Response(content="ok", media_type="text/plain")
        
    except Exception as e:
        print(f"❌ VK Callback error: {e}")
        return Response(content="ok", media_type="text/plain")

# 🔥 ТЕСТ ПОДТВЕРЖДЕНИЯ
@app.get("/vk_test_confirm")
async def vk_test_confirm():
    """Тестовый эндпоинт для проверки подтверждения"""
    print("🔥 VK CONFIRMATION TEST ENDPOINT HIT!")
    return Response(content="6da970f6", media_type="text/plain")

# 🔥 ПРОВЕРКА СЕРВЕРА
@app.get("/ping")
async def ping():
    return {"status": "alive", "message": "Сервер работает!"}

# ОСНОВНОЙ ФУНКЦИОНАЛ
class DreamRequest(BaseModel):
    user_id: str
    dream_text: str
    user_name: str = "Аноним"
    is_follow_up: bool = False

def init_db():
    conn = sqlite3.connect('dreams.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user_id TEXT UNIQUE,
            name TEXT,
            birth_date TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dreams (
            id INTEGER PRIMARY KEY,
            user_id TEXT,
            dream_text TEXT,
            interpretation TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    conn.commit()
    conn.close()

@app.post("/interpret")
async def interpret_dream(request: DreamRequest):
    try:
        if request.is_follow_up:
            enhanced_prompt = f"Пользователь хочет более глубокого анализа предыдущего сна: {request.dream_text}. Дай развернутый психологический анализ."
        else:
            enhanced_prompt = request.dream_text
        
        interpretation = gigachat.interpret_dream(
            dream_text=enhanced_prompt,
            user_name=request.user_name,
            user_context=f"ID: {request.user_id}"
        )
        
        conn = sqlite3.connect('dreams.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)",
            (request.user_id, request.user_name)
        )
        cursor.execute(
            "INSERT INTO dreams (user_id, dream_text, interpretation) VALUES (?, ?, ?)",
            (request.user_id, request.dream_text, interpretation)
        )
        conn.commit()
        conn.close()
        
        return {"interpretation": interpretation}
    
    except Exception as e:
        print(f"❌ Interpretation error: {e}")
        return {"interpretation": "❌ Ошибка при обработке сна"}

@app.get("/history/{user_id}")
async def get_history(user_id: str):
    try:
        conn = sqlite3.connect('dreams.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT dream_text, interpretation, timestamp FROM dreams WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10",
            (user_id,)
        )
        dreams = cursor.fetchall()
        conn.close()
        return {"dreams": dreams}
    except Exception as e:
        print(f"❌ History error: {e}")
        return {"dreams": []}

@app.get("/")
async def root():
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    else:
        return {
            "message": "🔮 ИИ Сонник API работает!",
            "endpoints": {
                "vk_simple": "GET /vk_simple?user_id=123&text=привет",
                "send_vk": "GET /send_vk?user_id=123&message=текст",
                "test_vk": "GET /test_vk?user_id=123&message=текст",
                "ping": "GET /ping",
                "vk_test_confirm": "GET /vk_test_confirm"
            },
            "vk_status": "initialized" if vk_bot else "not_initialized"
        }

@app.on_event("startup")
async def startup_event():
    init_db()
    print("✅ База данных инициализирована")

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("\n✅ Сервер остановлен!")
        os._exit(0)