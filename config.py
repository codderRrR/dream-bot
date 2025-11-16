import os
from dotenv import load_dotenv

load_dotenv()

# VK API настройки
VK_GROUP_TOKEN = os.getenv("VK_GROUP_TOKEN")
VK_CONFIRMATION_TOKEN = os.getenv("VK_CONFIRMATION_TOKEN", "877dbb3e")

# Telegram настройки
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8309048632:AAHAyHsfdvhjju6XxMYqwpwQ1oijKOA6EgY")

# GigaChat настройки
GIGACHAT_AUTH_KEY = os.getenv("GIGACHAT_AUTH_KEY", "MDE5YTgyMTYtYjQzOS03YTIyLWEwNjktMzU2NTBjYzhlOGM5OjMyNGJlNTg4LTg1Y2YtNGYxMi05OTFhLTIwY2UwNzAwZWE0NQ==")
GIGACHAT_SCOPE = "GIGACHAT_API_PERS"

# База данных
DATABASE_PATH = "dreams.db"

# Лимиты
FREE_REQUESTS_LIMIT = 15
ADMIN_IDS = [822018853]

# Сервер
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))