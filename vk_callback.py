import requests
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# ТВОЙ ТОКЕН ИЗ .env
VK_GROUP_TOKEN = "vk1.a.K_Sth5UQhK8Qu5fzlHnmCnMEVt_CbOzhQYNhl93BIzypJ1RZuiGE5pLJ6-Sae2ghchmMA9Ulq7VhNkHoGkvzHlUCX-nY4JfjvPeH-L3l9lzZGL09iYwz-XTAPUXToLZpZMZrRNdVrmD4Mwj2is05CJrhyBznBVaWDtHUviyM71bslN7WXWm4Z5QTOBtVkplaGrt9RrmkjIiI6Lld0h2m-Q"
CONFIRMATION_TOKEN = "123456"  # ⬅️ ЗАМЕНИ НА РЕАЛЬНЫЙ КОД ИЗ VK
API_URL = "http://localhost:8000"

def send_vk_message(user_id, message):
    """Отправка сообщения в VK"""
    url = "https://api.vk.com/method/messages.send"
    
    payload = {
        "user_id": user_id,
        "message": message,
        "random_id": 0,
        "access_token": VK_GROUP_TOKEN,
        "v": "5.199"
    }
    
    try:
        response = requests.post(url, data=payload)
        return response.json()
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return None

def handle_vk_message(user_id, text):
    """Обработка сообщения от пользователя"""
    try:
        # Отправляем запрос к нашему API
        response = requests.post(f"{API_URL}/interpret", json={
            "user_id": f"vk_{user_id}",
            "dream_text": text,
            "user_name": f"VK_User_{user_id}"
        })
        
        if response.status_code == 200:
            return response.json()["interpretation"]
        else:
            return "❌ Ошибка при обработке сна"
            
    except Exception as e:
        print(f"❌ Ошибка обработки: {e}")
        return "❌ Произошла ошибка, попробуйте позже"

@app.route('/vk_callback', methods=['POST', 'GET'])
def vk_callback():
    """Обработчик Callback API от VK"""
    if request.method == 'GET':
        # Подтверждение сервера
        confirmation_code = request.args.get('confirmation_code')
        if confirmation_code:
            return CONFIRMATION_TOKEN
        return 'ok'
    
    data = request.get_json()
    print(f"🔧 VK Callback: {data}")
    
    if data.get('type') == 'confirmation':
        return CONFIRMATION_TOKEN
    
    elif data.get('type') == 'message_new':
        message_data = data['object']['message']
        user_id = message_data['from_id']
        text = message_data['text']
        
        print(f"🔧 Новое сообщение от {user_id}: {text}")
        
        # Обрабатываем сообщение
        response_text = handle_vk_message(user_id, text)
        
        # Отправляем ответ
        send_vk_message(user_id, response_text)
        
        return 'ok'
    
    return 'ok'

if __name__ == '__main__':
    app.run(port=5000, debug=True)