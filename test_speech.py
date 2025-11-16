# test_speech.py - для проверки работы речевых функций
import sys
import os
sys.path.append(os.path.dirname(__file__))

from speech_processor import SpeechProcessor

def test_speech_processor():
    print("🔊 Тестируем SpeechProcessor...")
    
    sp = SpeechProcessor()
    
    print(f"✅ ASR доступен: {sp.is_asr_available()}")
    print(f"✅ TTS доступен: {sp.is_tts_available()}")
    
    # Тест TTS
    if sp.is_tts_available():
        print("🔊 Тестируем синтез речи...")
        audio_data = sp.text_to_speech("Привет! Это тест синтеза речи.")
        if audio_data:
            print("✅ TTS работает! Аудио сгенерировано.")
            with open("test_audio.mp3", "wb") as f:
                f.write(audio_data)
            print("✅ Аудио сохранено как test_audio.mp3")
        else:
            print("❌ TTS не сработал")
    else:
        print("⚠️ TTS недоступен")
    
    print("🎯 SpeechProcessor готов к работе!")

if __name__ == "__main__":
    test_speech_processor()