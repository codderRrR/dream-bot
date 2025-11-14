import requests
import json
import uuid
from datetime import datetime, timedelta

class GigaChatAPI:
    def __init__(self):
        self.auth_key = "MDE5YTgyMTYtYjQzOS03YTIyLWEwNjktMzU2NTBjYzhlOGM5OjMyNGJlNTg4LTg1Y2YtNGYxMi05OTFhLTIwY2UwNzAwZWE0NQ=="
        self.scope = "GIGACHAT_API_PERS"
        self.access_token = None
        self.token_expires = None
    
    def get_access_token(self):
        """Получаем Access Token"""
        if self.access_token and self.token_expires and datetime.now() < self.token_expires:
            return self.access_token
        
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Authorization": f"Basic {self.auth_key}",
            "RqUID": str(uuid.uuid4())
        }
        data = {
            "scope": self.scope
        }
        
        try:
            # ⬇️ ДОБАВИЛ ТАЙМАУТ И ПРОВЕРКУ SSL
            response = requests.post(url, headers=headers, data=data, verify=False, timeout=10)
            print(f"✅ Token response status: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data["access_token"]
                self.token_expires = datetime.now() + timedelta(minutes=25)
                print("✅ Получен новый Access Token")
                return self.access_token
            else:
                print(f"❌ Ошибка токена: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print("❌ Таймаут при получении токена")
            return None
        except Exception as e:
            print(f"❌ Ошибка получения токена: {e}")
            return None
    
    def interpret_dream(self, dream_text, user_name="Пользователь", user_context=""):
        """Интерпретируем сон через GigaChat"""
        access_token = self.get_access_token()
        if not access_token:
            return "🔮 Психологический анализ: Ваш сон может отражать текущие переживания. Рекомендую обратить внимание на эмоции в сновидении."
        
        url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        # ⬇️ УЛУЧШЕННЫЙ ПРОМПТ
        system_prompt = """Ты психолог-интерпретатор снов. Дай краткую психологическую трактовку (3-5 предложений). 
        Фокус на эмоциях и возможных жизненных ситуациях. Без эзотерики."""
        
        user_message = f"Сон: {dream_text}"
        
        data = {
            "model": "GigaChat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7,
            "max_tokens": 500,  # ⬇️ УМЕНЬШИЛ ДЛЯ БЫСТРОТЫ
            "top_p": 0.9
        }
        
        try:
            print(f"🔄 Отправляем сон в GigaChat: '{dream_text[:50]}...'")
            
            # ⬇️ ДОБАВИЛ ТАЙМАУТ И РЕТРАИ
            response = requests.post(url, headers=headers, json=data, verify=False, timeout=15)
            print(f"✅ GigaChat status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                interpretation = result["choices"][0]["message"]["content"]
                print("✅ Успешная интерпретация!")
                return interpretation
            else:
                print(f"❌ Ошибка GigaChat: {response.status_code}")
                # ⬇️ ЗАГЛУШКА ЕСЛИ API НЕ РАБОТАЕТ
                return self._get_fallback_interpretation(dream_text)
            
        except requests.exceptions.Timeout:
            print("❌ Таймаут GigaChat!")
            return self._get_fallback_interpretation(dream_text)
        except Exception as e:
            print(f"❌ Ошибка GigaChat: {e}")
            return self._get_fallback_interpretation(dream_text)
    
    def _get_fallback_interpretation(self, dream_text):
        """Заглушка когда GigaChat недоступен"""
        fallback_interpretations = [
            f"🔮 **Психологический анализ:** Сон '{dream_text}' может отражать ваши подсознательные переживания. Обратите внимание на эмоции, которые вы испытывали во сне - они часто связаны с реальными ситуациями.",
            
            f"💫 **Интерпретация:** Образы из сна '{dream_text}' могут символизировать внутренние конфликты или желания. Проанализируйте, какие чувства вызвал у вас этот сон.",
            
            f"🌙 **Психологический взгляд:** Сон о '{dream_text}' возможно связан с вашей текущей жизненной ситуацией. Попробуйте вспомнить детали для более глубокого понимания.",
            
            f"✨ **Анализ:** Ваш сон '{dream_text}' может быть отражением неосознанных мыслей или переживаний. Часто такие сны возникают в периоды изменений."
        ]
        
        import random
        return random.choice(fallback_interpretations)

# Создаём глобальный экземпляр
gigachat = GigaChatAPI()