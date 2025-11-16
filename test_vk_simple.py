# test_vk_simple.py - простая проверка VK бота
import sys
import os
sys.path.append(os.path.dirname(__file__))

from vk_bot import VKBot

def simple_test():
    print("🧪 Простой тест VK Bot...")
    
    bot = VKBot("test_token")
    
    # Тест основных функций
    test_cases = [
        (822018853, "привет"),
        (822018853, "📖 Интерпретировать сон"),
        (822018853, "👑 Админка"),
    ]
    
    for user_id, message in test_cases:
        print(f"🔧 Тест: '{message}'")
        try:
            response, keyboard = bot.process_message(user_id, message)
            print(f"✅ Успех: {response[:50]}...")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    print("🎯 Простой тест завершен!")

if __name__ == "__main__":
    simple_test()