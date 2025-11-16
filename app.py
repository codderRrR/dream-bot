from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

VK_GROUP_TOKEN = os.getenv("VK_GROUP_TOKEN")
# УБИРАЕМ ПОДТВЕРЖДЕНИЕ ИЗ FLASK - ОНО ТОЛЬКО В FASTAPI!
CONFIRMATION_TOKEN = "f2fb82fd"  # ОСТАВЛЯЕМ ДЛЯ СОВМЕСТИМОСТИ

@app.route('/ping')
def ping():
    return jsonify({"status": "alive", "message": "Сервер работает!"})

@app.route('/')
def root():
    return jsonify({"message": "VK Dream Bot API", "status": "running"})

@app.route('/vk_callback', methods=['GET', 'POST'])
def vk_callback():
    """Flask callback - ПЕРЕНАПРАВЛЯЕМ НА FASTAPI"""
    # ПЕРЕНАПРАВЛЯЕМ ВСЕ ЗАПРОСЫ НА FASTAPI СЕРВЕР
    return jsonify({
        "message": "Use FastAPI server on port 8000 for VK callbacks",
        "fastapi_url": "http://localhost:8000/vk_callback"
    })

@app.route('/test')
def test():
    """Тестовый маршрут"""
    return jsonify({
        "status": "flask_ok",
        "message": "Flask server is running on port 5000"
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)