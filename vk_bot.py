import requests
import json
import logging
from datetime import datetime
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VKBot:
    def __init__(self, group_token: str, api_url: str = "http://localhost:8000"):
        self.group_token = group_token
        self.api_url = api_url
        self.api_version = "5.199"
        
    def send_message(self, user_id: int, message: str, keyboard: Dict = None):
        """Отправка сообщения пользователю"""
        url = "https://api.vk.com/method/messages.send"
        
        random_id = int(datetime.now().timestamp() * 1000)
        
        payload = {
            "user_id": user_id,
            "message": message,
            "random_id": random_id,
            "access_token": self.group_token,
            "v": self.api_version
        }
        
        if keyboard:
            payload["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
        
        try:
            response = requests.post(url, data=payload)
            result = response.json()
            
            print(f"🔧 VK API Response: {result}")
            
            if "error" in result:
                error_msg = result["error"]
                logger.error(f"VK API Error: {error_msg}")
                return False
                
            if "response" in result:
                logger.info(f"✅ Сообщение отправлено пользователю {user_id}")
                return True
            else:
                logger.error(f"❌ Unexpected VK response: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Send message error: {e}")
            return False
    
    def get_default_keyboard(self):
        """Клавиатура с основными командами"""
        return {
            "one_time": False,
            "buttons": [
                [
                    {
                        "action": {
                            "type": "text",
                            "label": "📖 Интерпретировать сон"
                        },
                        "color": "primary"
                    }
                ],
                [
                    {
                        "action": {
                            "type": "text", 
                            "label": "📚 История снов"
                        },
                        "color": "secondary"
                    },
                    {
                        "action": {
                            "type": "text",
                            "label": "ℹ️ Помощь"
                        },
                        "color": "secondary"
                    }
                ]
            ]
        }
    
    def handle_message(self, user_id: int, message_text: str) -> str:
        """Обработка входящих сообщений"""
        message_text = message_text.lower().strip()
        
        # Приветственные команды
        if message_text in ["начать", "start", "привет", "сонник"]:
            return (
                "🔮 Добро пожаловать в ИИ Сонник!\n\n"
                "Я помогу вам понять ваши сны с психологической точки зрения.\n\n"
                "✨ Просто опишите свой сон, и я дам профессиональную интерпретацию!\n\n"
                "📖 Пример: \"Мне приснилось, что я летаю над городом...\"\n\n"
                "💫 После интерпретации можете писать: \"глубже\", \"подробнее\""
            )
        
        # Команда помощи
        elif message_text in ["помощь", "help", "команды"]:
            return (
                "📖 Доступные команды:\n\n"
                "• Просто опишите свой сон для интерпретации\n"
                "• «История снов» - ваши предыдущие сны\n"
                "• «Помощь» - это сообщение\n\n"
                "✨ После интерпретации можете писать:\n"
                "«глубже», «подробнее», «объясни»"
            )
        
        # История снов
        elif message_text in ["история", "история снов", "мои сны"]:
            try:
                response = requests.get(f"{self.api_url}/history/vk_{user_id}")
                if response.status_code == 200:
                    dreams = response.json()["dreams"]
                    
                    if not dreams:
                        return "📝 У вас пока нет записанных снов."
                    
                    history_text = "📖 Ваша история снов:\n\n"
                    for i, dream in enumerate(dreams[:3], 1):
                        dream_text, interpretation, timestamp = dream
                        history_text += f"{i}. {dream_text[:50]}...\n"
                        history_text += f"   📅 {timestamp[:10]}\n\n"
                    
                    return history_text
                else:
                    return "❌ Ошибка при получении истории"
                    
            except Exception as e:
                logger.error(f"History error: {e}")
                return "❌ Произошла ошибка"
        
        # 🔥🔥🔥 ГЛАВНОЕ: ЛЮБОЙ ДРУГОЙ ТЕКСТ = ИНТЕРПРЕТАЦИЯ СНА 🔥🔥🔥
        else:
            try:
                print(f"🔧 Интерпретируем сон: {message_text}")
                
                response = requests.post(f"{self.api_url}/interpret", json={
                    "user_id": f"vk_{user_id}",
                    "dream_text": message_text,
                    "user_name": f"VK_User_{user_id}"
                })
                
                if response.status_code == 200:
                    data = response.json()
                    interpretation = data["interpretation"]
                    print(f"🔧 Получена интерпретация: {interpretation[:100]}...")
                    return interpretation
                else:
                    print(f"❌ Ошибка API: {response.status_code}")
                    return "❌ Ошибка при обработке сна. Попробуйте позже."
                    
            except Exception as e:
                logger.error(f"Interpretation error: {e}")
                return "❌ Произошла ошибка. Попробуйте позже."

# Глобальный экземпляр бота
vk_bot = None

def init_vk_bot(token: str):
    global vk_bot
    vk_bot = VKBot(token)
    return vk_bot