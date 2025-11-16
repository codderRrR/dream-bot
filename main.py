# main.py - УСКОРЕННАЯ ВЕРСИЯ С LIFESPAN

import logging
import os
import time
import asyncio
from datetime import datetime
from fastapi import FastAPI, Request, Response
from contextlib import asynccontextmanager
import uvicorn

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Глобальные переменные для бота
vk_bot = None

# VK CONFIRMATION TOKEN
VK_CONFIRMATION_TOKEN = "75eda98a"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global vk_bot
    
    try:
        logging.info("🚀 Запуск Dream Interpretation Bot...")
        
        # Инициализация VK Bot - ИМПОРТ ВНУТРИ ФУНКЦИИ
        from vk_bot import VKBot
        
        vk_token = "vk1.a.ztt5kCO4D6hZvJ0aOEXmfJGGiotGrxcBl1p_mMjX38NGO__ocfcjYGwgfWMyOl9L1xBMtmPrV3_-a8r6KhArKEApacDOQKK5smaW95bJ7iBtmu7ts1VxxPSX7ompZYcDOrKCJc-oSdlKJxxn2ft0m_f2ohroTubQNXEYKIq8Fi9LrVmeiG3Mcq_1jDt8dxFBlwrTwABHOuFuFAJLh4RjcQ"  
        vk_bot = VKBot(vk_token)
        logging.info("✅ VK Bot инициализирован")
        
        logging.info("🔥 Бот запущен и готов к работе!")
        yield
    except Exception as e:
        logging.error(f"❌ Ошибка инициализации: {e}")
        raise
    finally:
        # Shutdown
        logging.info("🛑 Остановка бота...")

# Инициализация FastAPI с lifespan
app = FastAPI(title="Dream Interpretation Bot", lifespan=lifespan)

@app.get("/")
async def root():
    """Корневой маршрут"""
    return {"status": "online", "service": "Dream Interpretation Bot"}

@app.get("/ping")
async def ping():
    """Проверка работы сервера"""
    return {"status": "alive", "message": "Сервер работает!"}

async def send_message_async(user_id: int, message: str, keyboard: dict = None):
    """Асинхронная отправка сообщения"""
    try:
        if vk_bot:
            await asyncio.to_thread(vk_bot.send_message, user_id, message, keyboard)
    except Exception as e:
        logging.error(f"❌ Ошибка отправки сообщения: {e}")

@app.api_route("/vk_callback", methods=["GET", "POST"])
async def vk_callback(request: Request):
    """УСКОРЕННЫЙ обработчик callback от VK"""
    start_time = time.time()
    
    try:
        # ДЛЯ GET ЗАПРОСА (ПОДТВЕРЖДЕНИЕ) - СУПЕРБЫСТРО
        if request.method == "GET":
            params = dict(request.query_params)
            
            if params.get("confirmation_token") == VK_CONFIRMATION_TOKEN:
                logging.info(f"✅ Быстрое подтверждение за {time.time() - start_time:.3f} сек")
                return Response(content=VK_CONFIRMATION_TOKEN, media_type="text/plain")
            else:
                logging.error(f"❌ Неверный токен подтверждения: {params.get('confirmation_token')}")
                return Response(content="invalid token", status_code=400)
        
        # ДЛЯ POST ЗАПРОСА (СООБЩЕНИЯ)
        elif request.method == "POST":
            data = await request.json()
            
            # ПРОВЕРЯЕМ ТИП СОБЫТИЯ
            if data.get("type") == "confirmation":
                logging.info("✅ Подтверждение от VK")
                return Response(content=VK_CONFIRMATION_TOKEN, media_type="text/plain")
            
            elif data.get("type") == "message_new":
                message_data = data["object"]["message"]
                user_id = message_data["from_id"]
                text = message_data.get("text", "")
                attachments = message_data.get("attachments", [])
                
                logging.info(f"🔧 Новое сообщение от {user_id}: '{text}' | Вложения: {len(attachments)}")
                
                if vk_bot:
                    # БЫСТРАЯ ОБРАБОТКА
                    response_text, keyboard = vk_bot.process_message(user_id, text, attachments)
                    
                    # АСИНХРОННАЯ ОТПРАВКА ОТВЕТА
                    if response_text and response_text.strip():
                        # Запускаем отправку в фоне чтобы не блокировать ответ
                        asyncio.create_task(
                            send_message_async(user_id, response_text, keyboard)
                        )
                    else:
                        logging.warning("⚠️ Пустой ответ от бота")
                
                total_time = time.time() - start_time
                logging.info(f"✅ Callback обработан за {total_time:.3f} сек")
                return Response(content='ok', media_type="text/plain")
            
            # ДЛЯ ЛЮБОГО ДРУГОГО СОБЫТИЯ
            logging.info(f"🔧 Другое событие VK: {data.get('type')}")
            return Response(content='ok', media_type="text/plain")
        
    except Exception as e:
        logging.error(f"❌ VK Callback error: {e}")
        import traceback
        logging.error(f"❌ Traceback: {traceback.format_exc()}")
        return Response(content='ok', media_type="text/plain")

# ДОПОЛНИТЕЛЬНЫЕ МАРШРУТЫ ДЛЯ МОНИТОРИНГА
@app.get("/status")
async def status():
    """Статус системы"""
    return {
        "status": "online",
        "service": "Dream Interpretation Bot", 
        "timestamp": time.time(),
        "vk_bot_initialized": vk_bot is not None
    }

@app.get("/health")
async def health_check():
    """Health check для мониторинга"""
    return {
        "status": "healthy",
        "database": "connected" if vk_bot and hasattr(vk_bot, 'conn') else "disconnected",
        "gigachat": "available",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == '__main__':
    # Запуск сервера
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    logging.info(f"🚀 Starting server on {host}:{port}")
    logging.info(f"🔑 VK Confirmation Token: {VK_CONFIRMATION_TOKEN}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True
    )