import io
import requests
import tempfile
import os
import logging

# НАСТРАИВАЕМ ЛОГГИРОВАНИЕ
logger = logging.getLogger(__name__)

class SpeechProcessor:
    def __init__(self):
        self.recognizer = None
        self.tts_engine = None
        self.setup_speech_apis()
    
    def setup_speech_apis(self):
        """НАСТРОЙКА РЕЧЕВЫХ API С РЕЗЕРВНЫМИ ВАРИАНТАМИ"""
        try:
            # ИМПОРТИРУЕМ В КОНСТРУКТОРЕ
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            logger.info("✅ SpeechRecognition инициализирован")
        except ImportError:
            logger.warning("⚠️ SpeechRecognition не установлен, ASR недоступен")
            self.recognizer = None
        
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            # НАСТРОЙКА ГОЛОСА
            voices = self.tts_engine.getProperty('voices')
            if voices:
                self.tts_engine.setProperty('voice', voices[0].id)
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.8)
            logger.info("✅ pyttsx3 инициализирован")
        except ImportError:
            logger.warning("⚠️ pyttsx3 не установлен, TTS недоступен")
            self.tts_engine = None
    
    def speech_to_text(self, audio_data):
        """ПРЕОБРАЗОВАНИЕ РЕЧИ В ТЕКСТ С РЕЗЕРВНЫМИ ВАРИАНТАМИ"""
        if not self.recognizer:
            return "❌ Распознавание речи недоступно. Установите SpeechRecognition."
        
        try:
            # ИМПОРТИРУЕМ ВНУТРИ МЕТОДА
            import speech_recognition as sr
            from pydub import AudioSegment
            
            # ОБРАБОТКА AUDIO СООБЩЕНИЙ VK
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_audio:
                temp_audio.write(audio_data)
                temp_audio.flush()
                
                # КОНВЕРТИРУЕМ OGG В WAV
                audio = AudioSegment.from_ogg(temp_audio.name)
                wav_data = io.BytesIO()
                audio.export(wav_data, format="wav")
                wav_data.seek(0)
                
                # РАСПОЗНАВАНИЕ РЕЧИ
                with sr.AudioFile(wav_data) as source:
                    audio_record = self.recognizer.record(source)
                    text = self.recognizer.recognize_google(audio_record, language="ru-RU")
                
                os.unlink(temp_audio.name)
                return text
                
        except ImportError:
            # РЕЗЕРВНЫЙ ВАРИАНТ БЕЗ PYDUB
            logger.warning("⚠️ Pydub не установлен, используем упрощенную обработку")
            return "🔊 Голосовое сообщение получено. Для распознавания установите pydub."
            
        except Exception as e:
            logger.error(f"❌ Ошибка распознавания речи: {e}")
            return f"❌ Ошибка распознавания: {str(e)}"
    
    def text_to_speech(self, text, filename="response.mp3"):
        """ПРЕОБРАЗОВАНИЕ ТЕКСТА В РЕЧЬ"""
        if not self.tts_engine:
            return None
        
        try:
            self.tts_engine.save_to_file(text, filename)
            self.tts_engine.runAndWait()
            
            with open(filename, 'rb') as f:
                audio_data = f.read()
            
            os.remove(filename)
            return audio_data
            
        except Exception as e:
            logger.error(f"❌ Ошибка синтеза речи: {e}")
            return None
    
    def is_tts_available(self):
        """ПРОВЕРКА ДОСТУПНОСТИ TTS"""
        return self.tts_engine is not None
    
    def is_asr_available(self):
        """ПРОВЕРКА ДОСТУПНОСТИ ASR"""
        return self.recognizer is not None