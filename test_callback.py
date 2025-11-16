
import requests
import json

def test_vk_callback():
    """Тестируем VK callback"""
    print("🔧 Тестируем VK Callback API...")
    
    # ТЕСТ ПОДТВЕРЖДЕНИЯ
    confirmation_url = "http://localhost:8000/vk_callback"
    test_params = {
        "confirmation_token": "75eda98a",
        "group_id": "123456"
    }
    
    try:
        response = requests.get(confirmation_url, params=test_params)
        print(f"✅ Confirmation Response: {response.status_code}")
        print(f"✅ Response Text: {response.text}")
        
        if response.text == "75eda98a":
            print("🎉 CONFIRMATION SUCCESS! VK callback настроен правильно!")
        else:
            print(f"❌ CONFIRMATION FAILED! Expected '75eda98a', got '{response.text}'")
            
    except Exception as e:
        print(f"❌ Error testing callback: {e}")

def test_server_status():
    """Тестируем статус серверов"""
    servers = [
        ("Flask", "http://localhost:5000/ping"),
        ("FastAPI", "http://localhost:8000/"),
        ("FastAPI Ping", "http://localhost:8000/ping")
    ]
    
    for name, url in servers:
        try:
            response = requests.get(url, timeout=5)
            print(f"✅ {name} ({url}): {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"❌ {name} ({url}): {e}")

if __name__ == "__main__":
    print("🚀 Запускаем тесты серверов...")
    test_server_status()
    print("\n🔧 Тестируем VK Callback...")
    test_vk_callback()