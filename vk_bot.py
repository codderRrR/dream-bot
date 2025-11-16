# vk_bot.py - ИСПРАВЛЕННАЯ ВЕРСИЯ С РАБОЧИМИ ЛОГАМИ

import logging
import sqlite3
import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, List
import threading

class VKBot:
    def __init__(self, token, db_path="dreams.db"):
        self.token = token
        self.db_path = db_path
        self.admin_ids = [822018853]
        self.free_requests_limit = 15
        self.response_cache = {}
        self.cache_ttl = 300
        
        self.init_database()
        self.preload_gigachat()
        
        logging.info("🚀 Ускоренный VK Bot инициализирован!")

    def preload_gigachat(self):
        """Предварительная загрузка GigaChat в фоне"""
        def load_in_background():
            try:
                from gigachat_api import gigachat
                gigachat.get_access_token()
                logging.info("✅ GigaChat предзагружен в фоне")
            except Exception as e:
                logging.warning(f"⚠️ Предзагрузка GigaChat: {e}")

        thread = threading.Thread(target=load_in_background)
        thread.daemon = True
        thread.start()

    def init_database(self):
        """Инициализация базы данных"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                requests_count INTEGER DEFAULT 0,
                is_subscribed BOOLEAN DEFAULT FALSE,
                is_blocked BOOLEAN DEFAULT FALSE,
                balance REAL DEFAULT 0.0,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_states (
                user_id INTEGER PRIMARY KEY,
                state TEXT,
                state_data TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dreams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                dream_text TEXT,
                interpretation TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message_type TEXT,
                message_text TEXT,
                direction TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                error_type TEXT,
                error_message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action_type TEXT,
                target_user_id INTEGER,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        logging.info("✅ База данных инициализирована!")

    # КЛАВИАТУРЫ
    def get_main_keyboard(self):
        return {
            "inline": False,
            "buttons": [
                [{"action": {"type": "text", "label": "📖 Интерпретировать сон"}, "color": "primary"}],
                [{"action": {"type": "text", "label": "📚 История снов"}, "color": "secondary"}],
                [{"action": {"type": "text", "label": "💎 Подписка"}, "color": "positive"}],
                [{"action": {"type": "text", "label": "👑 Админка"}, "color": "default"}]
            ]
        }

    def get_detailed_analysis_keyboard(self):
        return {
            "inline": False,
            "buttons": [
                [{"action": {"type": "text", "label": "📊 Подробнее"}, "color": "primary"}],
                [{"action": {"type": "text", "label": "💭 Эмоции"}, "color": "primary"}],
                [{"action": {"type": "text", "label": "🔍 Символы"}, "color": "secondary"}],
                [{"action": {"type": "text", "label": "🎯 Паттерны"}, "color": "secondary"}],
                [{"action": {"type": "text", "label": "🌟 Рекомендации"}, "color": "positive"}],
                [{"action": {"type": "text", "label": "🔙 Главное меню"}, "color": "negative"}]
            ]
        }

    def get_admin_keyboard(self):
        return {
            "inline": False,
            "buttons": [
                [{"action": {"type": "text", "label": "📊 Статистика"}, "color": "primary"}],
                [{"action": {"type": "text", "label": "👥 Все пользователи"}, "color": "primary"}],
                [{"action": {"type": "text", "label": "🔍 Поиск пользователей"}, "color": "secondary"}],
                [{"action": {"type": "text", "label": "📋 Логи"}, "color": "secondary"}],
                [{"action": {"type": "text", "label": "🔙 Выйти из админки"}, "color": "negative"}]
            ]
        }

    def get_logs_keyboard(self):
        """Клавиатура для раздела логов"""
        return {
            "inline": False,
            "buttons": [
                [{"action": {"type": "text", "label": "📨 Логи сообщений"}, "color": "primary"}],
                [{"action": {"type": "text", "label": "❌ Логи ошибок"}, "color": "primary"}],
                [{"action": {"type": "text", "label": "👑 Логи действий"}, "color": "primary"}],
                [{"action": {"type": "text", "label": "🔙 Назад в админку"}, "color": "negative"}]
            ]
        }

    def get_cancel_keyboard(self):
        return {
            "inline": False,
            "buttons": [
                [{"action": {"type": "text", "label": "❌ Отмена"}, "color": "negative"}]
            ]
        }

    # ОСНОВНЫЕ МЕТОДЫ
    def log_message(self, user_id: int, message_type: str, message_text: str, direction: str):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO message_logs (user_id, message_type, message_text, direction)
                VALUES (?, ?, ?, ?)
            ''', (user_id, message_type, message_text, direction))
            self.conn.commit()
        except Exception as e:
            logging.error(f"❌ Ошибка логирования сообщения: {e}")

    def update_user_activity(self, user_id: int):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, last_activity)
                VALUES (?, datetime('now'))
            ''', (user_id,))
            self.conn.commit()
        except Exception as e:
            logging.error(f"❌ Ошибка обновления активности: {e}")

    def get_user_state(self, user_id: int) -> str:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT state FROM user_states WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else ""
        except Exception as e:
            logging.error(f"❌ Ошибка получения состояния: {e}")
            return ""

    def set_user_state(self, user_id: int, state: str, state_data: str = ""):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_states (user_id, state, state_data, updated_at)
                VALUES (?, ?, ?, datetime('now'))
            ''', (user_id, state, state_data))
            self.conn.commit()
        except Exception as e:
            logging.error(f"❌ Ошибка установки состояния: {e}")

    def get_user_requests_count(self, user_id: int) -> int:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT requests_count FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logging.error(f"❌ Ошибка получения количества запросов: {e}")
            return 0

    def increment_user_requests(self, user_id: int):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, requests_count, last_activity)
                VALUES (?, COALESCE((SELECT requests_count FROM users WHERE user_id = ?), 0) + 1, datetime('now'))
            ''', (user_id, user_id))
            self.conn.commit()
        except Exception as e:
            logging.error(f"❌ Ошибка увеличения счетчика запросов: {e}")

    def get_last_dream_text(self, user_id: int) -> str:
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT dream_text FROM dreams 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            ''', (user_id,))
            result = cursor.fetchone()
            return result[0] if result else ""
        except Exception as e:
            logging.error(f"❌ Ошибка получения последнего сна: {e}")
            return ""

    def interpret_dream(self, user_id: int, dream_text: str, analysis_type: str = "basic") -> str:
        cache_key = f"{user_id}_{hash(dream_text)}_{analysis_type}"
        
        if cache_key in self.response_cache:
            cached_time, interpretation = self.response_cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                logging.info("✅ Используем кэшированную интерпретацию")
                return interpretation
        
        try:
            from gigachat_api import gigachat
            interpretation = gigachat.interpret_dream(
                dream_text=dream_text,
                user_id=user_id,
                user_name="Пользователь",
                analysis_type=analysis_type
            )
            
            self.response_cache[cache_key] = (time.time(), interpretation)
            return interpretation
            
        except Exception as e:
            logging.error(f"❌ Ошибка интерпретации: {e}")
            fallbacks = {
                "эмоции": f"💭 **ЭМОЦИОНАЛЬНЫЙ АНАЛИЗ**\n\nСон '{dream_text}' отражает ваши текущие переживания.",
                "рекомендации": f"🌟 **ПРАКТИЧЕСКИЕ РЕКОМЕНДАЦИИ**\n\nДля работы со сном '{dream_text}': ведите дневник сновидений.",
                "символы": f"🔍 **АНАЛИЗ СИМВОЛОВ**\n\nКлючевые образы сна '{dream_text}' несут важную информацию.",
                "подробнее": f"📊 **ДЕТАЛЬНЫЙ АНАЛИЗ**\n\nСон '{dream_text}' содержит глубинные аспекты для анализа.",
                "паттерны": f"🎯 **АНАЛИЗ ПАТТЕРНОВ**\n\nВ сне '{dream_text}' могут присутствовать повторяющиеся темы."
            }
            return fallbacks.get(analysis_type, f"🔮 **ИНТЕРПРЕТАЦИЯ СНА**\n\nСон '{dream_text}' отражает ваши внутренние состояния.")

    def process_message(self, user_id: int, text: str, attachments: list = None) -> Tuple[str, dict]:
        start_time = time.time()
        
        try:
            self.update_user_activity(user_id)
            self.log_message(user_id, "text", text, "incoming")
            
            quick_responses = {
                "привет": ("🔮 Добро пожаловать! Выберите действие:", self.get_main_keyboard()),
                "start": ("🔮 Добро пожаловать! Выберите действие:", self.get_main_keyboard()),
                "помощь": ("📋 Доступные команды:\n• 📖 Интерпретировать сон\n• 📚 История снов\n• 💎 Подписка\n• 👑 Админка", self.get_main_keyboard()),
            }
            
            text_lower = text.lower().strip()
            if text_lower in quick_responses:
                return quick_responses[text_lower]
            
            response_text, keyboard = self.process_text_message(user_id, text)
            
            processing_time = time.time() - start_time
            logging.info(f"✅ Сообщение обработано за {processing_time:.3f} сек")
            
            return response_text, keyboard
            
        except Exception as e:
            logging.error(f"❌ Ошибка обработки: {e}")
            return "Произошла ошибка. Попробуйте еще раз.", self.get_main_keyboard()

    def process_text_message(self, user_id: int, text: str) -> Tuple[str, dict]:
        text_lower = text.lower().strip()
        
        if text_lower in ["отмена", "назад", "cancel", "❌ отмена", "🔙 главное меню"]:
            return self.handle_cancel(user_id)

        analysis_commands = {
            "подробнее": "подробнее",
            "📊 подробнее": "подробнее", 
            "эмоции": "эмоции",
            "💭 эмоции": "эмоции",
            "символы": "символы", 
            "🔍 символы": "символы",
            "паттерны": "паттерны",
            "🎯 паттерны": "паттерны",
            "рекомендации": "рекомендации",
            "🌟 рекомендации": "рекомендации"
        }
        
        if text_lower in analysis_commands:
            analysis_type = analysis_commands[text_lower]
            return self.handle_detailed_analysis_request(user_id, analysis_type)

        user_state = self.get_user_state(user_id)
        is_admin = user_id in self.admin_ids
        
        logging.info(f"🔧 Состояние пользователя {user_id}: '{user_state}', текст: '{text}'")

        # ОБРАБОТКА СОСТОЯНИЙ ЛОГОВ
        if user_state.startswith("admin_logs"):
            return self.handle_admin_logs_state(user_id, text, user_state, is_admin)

        if user_state.startswith("admin_"):
            return self.handle_admin_state(user_id, text, user_state, is_admin)

        # ОСНОВНЫЕ КОМАНДЫ
        if text_lower in ["админка", "👑 админка"]:
            if is_admin:
                return self.handle_admin_panel(user_id)
            else:
                return "❌ У вас нет доступа к админ-панели", self.get_main_keyboard()
        
        if "интерпретировать сон" in text_lower or "📖" in text:
            return self.handle_dream_interpretation_start(user_id, is_admin)
        
        if "история снов" in text_lower or "📚" in text:
            return self.handle_user_dream_history(user_id)
        
        if "подписка" in text_lower or "💎" in text:
            return self.handle_user_subscription(user_id, is_admin)

        if user_state == "waiting_for_dream":
            return self.handle_dream_text(user_id, text, is_admin)

        if text_lower in ["выйти из админки", "🔙 выйти из админки"]:
            self.set_user_state(user_id, "")
            return self.handle_default_response(user_id, is_admin)

        return self.handle_default_response(user_id, is_admin)

    def handle_admin_logs_state(self, user_id: int, text: str, state: str, is_admin: bool) -> Tuple[str, dict]:
        """Обработка состояний раздела логов"""
        try:
            if text == "📨 Логи сообщений":
                return self.handle_message_logs(user_id)
            elif text == "❌ Логи ошибок":
                return self.handle_error_logs(user_id)
            elif text == "👑 Логи действий":
                return self.handle_action_logs(user_id)
            elif text == "🔙 Назад в админку":
                self.set_user_state(user_id, "admin_panel")
                return self.handle_admin_panel(user_id)
            else:
                return "❌ Неизвестная команда в разделе логов", self.get_logs_keyboard()
                
        except Exception as e:
            logging.error(f"❌ Ошибка обработки состояния логов: {e}")
            return "❌ Ошибка при обработке логов", self.get_admin_keyboard()

    def handle_message_logs(self, user_id: int) -> Tuple[str, dict]:
        """Логи сообщений"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT user_id, message_type, message_text, direction, timestamp 
                FROM message_logs 
                ORDER BY timestamp DESC 
                LIMIT 10
            ''')
            
            logs = cursor.fetchall()
            
            if not logs:
                return "📨 Логи сообщений пусты", self.get_logs_keyboard()
            
            logs_text = "📨 ПОСЛЕДНИЕ 10 ЛОГОВ СООБЩЕНИЙ:\n\n"
            
            for i, (log_user_id, msg_type, msg_text, direction, timestamp) in enumerate(logs, 1):
                direction_icon = "📥" if direction == "incoming" else "📤"
                logs_text += f"{i}. {direction_icon} {timestamp[:16]}\n"
                logs_text += f"   👤 User: {log_user_id}\n"
                logs_text += f"   💬 {msg_text[:50]}{'...' if len(msg_text) > 50 else ''}\n"
                logs_text += "─" * 30 + "\n"
            
            return logs_text, self.get_logs_keyboard()
            
        except Exception as e:
            logging.error(f"❌ Ошибка получения логов сообщений: {e}")
            return "❌ Ошибка при получении логов сообщений", self.get_logs_keyboard()

    def handle_error_logs(self, user_id: int) -> Tuple[str, dict]:
        """Логи ошибок"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT user_id, error_type, error_message, timestamp 
                FROM error_logs 
                ORDER BY timestamp DESC 
                LIMIT 10
            ''')
            
            logs = cursor.fetchall()
            
            if not logs:
                return "❌ Логи ошибок пусты", self.get_logs_keyboard()
            
            logs_text = "❌ ПОСЛЕДНИЕ 10 ЛОГОВ ОШИБОК:\n\n"
            
            for i, (log_user_id, error_type, error_msg, timestamp) in enumerate(logs, 1):
                logs_text += f"{i}. ⚠️ {timestamp[:16]}\n"
                logs_text += f"   👤 User: {log_user_id}\n"
                logs_text += f"   🔧 Тип: {error_type}\n"
                logs_text += f"   💬 {error_msg[:60]}{'...' if len(error_msg) > 60 else ''}\n"
                logs_text += "─" * 30 + "\n"
            
            return logs_text, self.get_logs_keyboard()
            
        except Exception as e:
            logging.error(f"❌ Ошибка получения логов ошибок: {e}")
            return "❌ Ошибка при получении логов ошибок", self.get_logs_keyboard()

    def handle_action_logs(self, user_id: int) -> Tuple[str, dict]:
        """Логи действий админов"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT admin_id, action_type, target_user_id, details, timestamp 
                FROM admin_actions 
                ORDER BY timestamp DESC 
                LIMIT 10
            ''')
            
            logs = cursor.fetchall()
            
            if not logs:
                return "👑 Логи действий админов пусты", self.get_logs_keyboard()
            
            logs_text = "👑 ПОСЛЕДНИЕ 10 ЛОГОВ ДЕЙСТВИЙ АДМИНОВ:\n\n"
            
            for i, (admin_id, action_type, target_id, details, timestamp) in enumerate(logs, 1):
                logs_text += f"{i}. 👑 {timestamp[:16]}\n"
                logs_text += f"   Админ: {admin_id}\n"
                logs_text += f"   Действие: {action_type}\n"
                logs_text += f"   Цель: {target_id if target_id else 'N/A'}\n"
                if details:
                    logs_text += f"   Детали: {details[:40]}{'...' if len(details) > 40 else ''}\n"
                logs_text += "─" * 30 + "\n"
            
            return logs_text, self.get_logs_keyboard()
            
        except Exception as e:
            logging.error(f"❌ Ошибка получения логов действий: {e}")
            return "❌ Ошибка при получении логов действий", self.get_logs_keyboard()

    def handle_detailed_analysis_request(self, user_id: int, analysis_type: str) -> Tuple[str, dict]:
        try:
            last_dream_text = self.get_last_dream_text(user_id)
            
            if not last_dream_text:
                return "❌ У вас нет последнего сна для анализа. Сначала опишите сон!", self.get_main_keyboard()
            
            logging.info(f"🔍 Запуск детального анализа типа: {analysis_type}")
            
            detailed_analysis = self.interpret_dream(user_id, last_dream_text, analysis_type)
            
            return detailed_analysis, self.get_detailed_analysis_keyboard()
            
        except Exception as e:
            logging.error(f"❌ Ошибка детального анализа: {e}")
            return "❌ Ошибка при детальном анализе. Попробуйте еще раз.", self.get_main_keyboard()

    def handle_cancel(self, user_id: int) -> Tuple[str, dict]:
        try:
            self.set_user_state(user_id, "")
            return "Действие отменено. Возврат в главное меню.", self.get_main_keyboard()
        except Exception as e:
            logging.error(f"❌ Ошибка отмены: {e}")
            return "Возврат в главное меню.", self.get_main_keyboard()

    def handle_default_response(self, user_id: int, is_admin: bool) -> Tuple[str, dict]:
        try:
            self.set_user_state(user_id, "")
            used_requests = self.get_user_requests_count(user_id)
            
            welcome_text = (
                f"{'👑 Добро пожаловать в Админ-панель!' if is_admin else '🔮 Добро пожаловать в мир сновидений!'}\n\n"
                f"{f'✅ У вас неограниченный доступ' if is_admin else f'📊 Использовано запросов: {used_requests}/{self.free_requests_limit}'}\n\n"
                f"Выберите действие:"
            )
            return welcome_text, self.get_main_keyboard()
        except Exception as e:
            logging.error(f"❌ Ошибка стандартного ответа: {e}")
            return "🔮 Добро пожаловать! Выберите действие:", self.get_main_keyboard()

    def handle_dream_interpretation_start(self, user_id: int, is_admin: bool) -> Tuple[str, dict]:
        try:
            if not is_admin:
                used_requests = self.get_user_requests_count(user_id)
                if used_requests >= self.free_requests_limit:
                    return self.show_subscription_offer(user_id, used_requests)
            
            self.set_user_state(user_id, "waiting_for_dream")
            return (
                "📝 Опишите свой сон подробнее, и я помогу его интерпретировать.\n\n"
                "Например: \"Я видел сон, что летал над городом...\"\n\n"
                "❌ Напишите 'Отмена' для возврата в меню",
                self.get_cancel_keyboard()
            )
        except Exception as e:
            logging.error(f"❌ Ошибка начала интерпретации сна: {e}")
            return "❌ Ошибка при начале интерпретации сна", self.get_main_keyboard()

    def handle_dream_text(self, user_id: int, text: str, is_admin: bool) -> Tuple[str, dict]:
        try:
            if not is_admin:
                self.increment_user_requests(user_id)
            
            interpretation = self.interpret_dream(user_id, text, "basic")
            
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO dreams (user_id, dream_text, interpretation)
                VALUES (?, ?, ?)
            ''', (user_id, text, interpretation))
            self.conn.commit()
            
            interpretation += "\n\n💫 **Хотите узнать больше? Используйте кнопки детального анализа ниже!**"
            
            return interpretation, self.get_detailed_analysis_keyboard()
            
        except Exception as e:
            logging.error(f"❌ Ошибка интерпретации сна: {e}")
            self.set_user_state(user_id, "")
            return "Произошла ошибка при интерпретации сна. Попробуйте еще раз.", self.get_main_keyboard()

    def handle_admin_panel(self, user_id: int) -> Tuple[str, dict]:
        try:
            stats = self.get_admin_stats()
            
            admin_text = (
                f"👑 АДМИН-ПАНЕЛЬ\n\n"
                f"📊 Статистика:\n"
                f"• Всего пользователей: {stats['total_users']}\n"
                f"• Всего запросов: {stats['total_requests']}\n"
                f"• Всего снов: {stats['total_dreams']}\n"
                f"• Активных сегодня: {stats['active_today']}\n\n"
                f"⚙️ Доступные команды:"
            )
            self.set_user_state(user_id, "admin_panel")
            return admin_text, self.get_admin_keyboard()
        except Exception as e:
            logging.error(f"❌ Ошибка админ-панели: {e}")
            return "❌ Ошибка при загрузке админ-панели", self.get_main_keyboard()

    def handle_admin_state(self, user_id: int, text: str, state: str, is_admin: bool) -> Tuple[str, dict]:
        try:
            logging.info(f"🔧 Обработка админского состояния: {state}, команда: {text}")
            
            if state == "admin_panel":
                if text == "📊 Статистика":
                    return self.handle_admin_stats_detailed(user_id)
                elif text == "👥 Все пользователи":
                    return self.handle_admin_users_list(user_id)
                elif text == "🔍 Поиск пользователей":
                    self.set_user_state(user_id, "admin_search")
                    return "🔍 Введите ID, имя, фамилию или username пользователя для поиска:", self.get_cancel_keyboard()
                elif text == "📋 Логи":
                    return self.handle_admin_logs_menu(user_id)
                elif text == "🔙 Выйти из админки":
                    self.set_user_state(user_id, "")
                    return self.handle_default_response(user_id, is_admin)
            
            elif state == "admin_search":
                if text == "❌ Отмена":
                    self.set_user_state(user_id, "admin_panel")
                    return self.handle_admin_panel(user_id)
                else:
                    return self.handle_admin_search_users(user_id, text)
            
            self.set_user_state(user_id, "admin_panel")
            return self.handle_admin_panel(user_id)
            
        except Exception as e:
            logging.error(f"❌ Ошибка обработки состояния админа: {e}")
            self.set_user_state(user_id, "admin_panel")
            return "Произошла ошибка", self.get_admin_keyboard()

    def handle_admin_logs_menu(self, user_id: int) -> Tuple[str, dict]:
        """Меню логов - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        logs_text = (
            "📋 СИСТЕМА ЛОГИРОВАНИЯ\n\n"
            "Доступные разделы:\n"
            "• 📨 Логи сообщений - история всех сообщений\n"
            "• ❌ Логи ошибок - системные ошибки и исключения\n"  
            "• 👑 Логи действий - действия администраторов\n\n"
            "Выберите раздел для просмотра:"
        )
        
        self.set_user_state(user_id, "admin_logs_menu")
        return logs_text, self.get_logs_keyboard()

    def handle_admin_stats_detailed(self, user_id: int) -> Tuple[str, dict]:
        try:
            stats = self.get_admin_stats()
            
            stats_text = (
                f"📊 ДЕТАЛЬНАЯ СТАТИСТИКА\n\n"
                f"👥 Пользователи:\n"
                f"• Всего: {stats['total_users']}\n"
                f"• Активных сегодня: {stats['active_today']}\n\n"
                f"🔮 Сны:\n"
                f"• Всего интерпретаций: {stats['total_dreams']}\n\n"
                f"📈 Активность:\n"
                f"• Всего запросов: {stats['total_requests']}\n"
            )
            
            self.set_user_state(user_id, "admin_stats")
            return stats_text, self.get_admin_keyboard()
            
        except Exception as e:
            logging.error(f"❌ Ошибка детальной статистики: {e}")
            return "❌ Ошибка при получении статистики", self.get_admin_keyboard()

    def handle_admin_users_list(self, user_id: int) -> Tuple[str, dict]:
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
                SELECT user_id, username, first_name, last_name, requests_count, is_subscribed, last_activity
                FROM users 
                ORDER BY last_activity DESC
                LIMIT 20
            ''')
            
            users = cursor.fetchall()
            
            if not users:
                return "📝 Нет зарегистрированных пользователей.", self.get_admin_keyboard()
            
            users_text = "👥 ВСЕ ПОЛЬЗОВАТЕЛИ:\n\n"
            
            for user in users:
                user_id, username, first_name, last_name, requests_count, is_subscribed, last_activity = user
                status = "💎 ПОДПИСКА" if is_subscribed else "🔓 БЕСПЛАТНО"
                name = f"{first_name or ''} {last_name or ''}".strip() or username or "Не указано"
                
                users_text += f"👤 {name}\n"
                users_text += f"🆔 ID: {user_id}\n"
                users_text += f"📊 Запросов: {requests_count}\n"
                users_text += f"🎯 Статус: {status}\n"
                users_text += f"🕐 Активность: {last_activity[:16]}\n"
                users_text += "─" * 30 + "\n"
            
            users_text += "\n📝 Введите ID пользователя для подробной информации"
            
            self.set_user_state(user_id, "admin_view_users")
            return users_text, self.get_admin_keyboard()
            
        except Exception as e:
            logging.error(f"❌ Ошибка получения списка пользователей: {e}")
            return "❌ Ошибка при получении списка пользователей", self.get_admin_keyboard()

    def handle_admin_search_users(self, user_id: int, search_query: str) -> Tuple[str, dict]:
        try:
            cursor = self.conn.cursor()
            
            search_pattern = f"%{search_query}%"
            cursor.execute('''
                SELECT user_id, username, first_name, last_name, requests_count, is_subscribed, last_activity
                FROM users 
                WHERE user_id = ? OR username LIKE ? OR first_name LIKE ? OR last_name LIKE ?
                ORDER BY last_activity DESC
                LIMIT 10
            ''', (search_query, search_pattern, search_pattern, search_pattern))
            
            users = cursor.fetchall()
            
            if not users:
                return f"❌ Пользователи по запросу '{search_query}' не найдены.", self.get_admin_keyboard()
            
            users_text = f"🔍 РЕЗУЛЬТАТЫ ПОИСКА: '{search_query}'\n\n"
            
            for user in users:
                user_id, username, first_name, last_name, requests_count, is_subscribed, last_activity = user
                status = "💎 ПОДПИСКА" if is_subscribed else "🔓 БЕСПЛАТНО"
                name = f"{first_name or ''} {last_name or ''}".strip() or username or "Не указано"
                
                users_text += f"👤 {name}\n"
                users_text += f"🆔 ID: {user_id}\n"
                users_text += f"📊 Запросов: {requests_count}\n"
                users_text += f"🎯 Статус: {status}\n"
                users_text += f"🕐 Активность: {last_activity[:16]}\n"
                users_text += "─" * 30 + "\n"
            
            users_text += "\n📝 Введите ID пользователя для подробной информации"
            
            self.set_user_state(user_id, "admin_view_users")
            return users_text, self.get_admin_keyboard()
            
        except Exception as e:
            logging.error(f"❌ Ошибка поиска пользователей: {e}")
            return "❌ Ошибка при поиске пользователей", self.get_admin_keyboard()

    def handle_user_dream_history(self, user_id: int) -> Tuple[str, dict]:
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
                SELECT dream_text, interpretation, created_at 
                FROM dreams 
                WHERE user_id = ? 
                ORDER BY created_at DESC
                LIMIT 5
            ''', (user_id,))
            
            dreams = cursor.fetchall()
            
            if not dreams:
                return "📝 У вас пока нет сохраненных снов. Начните с интерпретации первого сна!", self.get_main_keyboard()
            
            dreams_text = "📚 ВАША ИСТОРИЯ СНОВ:\n\n"
            
            for i, (dream_text, interpretation, created_at) in enumerate(dreams, 1):
                dreams_text += f"🔮 Сон #{i} ({created_at[:16]}):\n"
                dreams_text += f"💭 {dream_text[:100]}{'...' if len(dream_text) > 100 else ''}\n"
                dreams_text += "─" * 30 + "\n\n"
            
            dreams_text += f"📊 Всего сохраненных снов: {len(dreams)}"
            
            return dreams_text, self.get_main_keyboard()
            
        except Exception as e:
            logging.error(f"❌ Ошибка получения истории снов: {e}")
            return "❌ Ошибка при получении истории снов", self.get_main_keyboard()

    def handle_user_subscription(self, user_id: int, is_admin: bool) -> Tuple[str, dict]:
        try:
            if is_admin:
                subscription_text = (
                    f"👑 ВАША ПОДПИСКА\n\n"
                    f"✅ Статус: АКТИВИРОВАНА (Администратор)\n\n"
                    f"🔮 Доступные функции:\n"
                    f"• 🔥 Неограниченные интерпретации снов\n"
                    f"• 📊 Расширенный анализ сновидений\n"
                    f"• 💫 Персональные рекомендации\n"
                    f"• 👑 Приоритетная поддержка\n"
                    f"• ⚡ Мгновенная обработка запросов\n\n"
                    f"🎯 У вас полный доступ ко всем функциям!"
                )
                return subscription_text, self.get_main_keyboard()
            else:
                used_requests = self.get_user_requests_count(user_id)
                
                subscription_text = (
                    f"💎 ПОДПИСКА\n\n"
                    f"📊 Использовано запросов: {used_requests}/{self.free_requests_limit}\n\n"
                    f"🔮 Премиум-функции:\n"
                    f"• 🔥 Неограниченные интерпретации снов\n"
                    f"• 📊 Расширенный анализ сновидений\n"
                    f"• 💫 Персональные рекомендации\n"
                    f"• ⚡ Мгновенная обработка запросов\n\n"
                    f"💳 Стоимость: 299 руб/месяц\n\n"
                    f"Для активации напишите: \"Оплатить\""
                )
                return subscription_text, self.get_main_keyboard()
        except Exception as e:
            logging.error(f"❌ Ошибка обработки подписки: {e}")
            return "❌ Ошибка при обработке подписки", self.get_main_keyboard()

    def show_subscription_offer(self, user_id: int, used_requests: int) -> Tuple[str, dict]:
        subscription_text = (
            f"🚫 БЕСПЛАТНЫЙ ЛИМИТ ИСЧЕРПАН\n\n"
            f"Вы использовали {used_requests} бесплатных интерпретаций снов.\n\n"
            f"💎 Для продолжения работы активируйте подписку:\n"
            f"Всего 299 руб/месяц за неограниченное количество анализов снов!\n\n"
            f"Напишите \"Подписка\" для активации"
        )
        return subscription_text, self.get_main_keyboard()

    def get_admin_stats(self) -> Dict[str, int]:
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(requests_count) FROM users")
            total_requests = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT COUNT(*) FROM users WHERE date(last_activity) = date('now')")
            active_today = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM dreams")
            total_dreams = cursor.fetchone()[0]
            
            return {
                'total_users': total_users,
                'total_requests': total_requests,
                'active_today': active_today,
                'total_dreams': total_dreams
            }
        except Exception as e:
            logging.error(f"❌ Ошибка получения статистики: {e}")
            return {'total_users': 0, 'total_requests': 0, 'active_today': 0, 'total_dreams': 0}

    def send_message(self, user_id: int, message: str, keyboard: dict = None) -> bool:
        try:
            url = "https://api.vk.com/method/messages.send"
            payload = {
                "user_id": user_id,
                "message": message,
                "random_id": int(time.time() * 1000),
                "access_token": self.token,
                "v": "5.199"
            }
            
            if keyboard:
                payload["keyboard"] = json.dumps(keyboard)
            
            response = requests.post(url, data=payload, timeout=10)
            result = response.json()
            
            if 'error' in result:
                logging.error(f"❌ VK API Error: {result['error']}")
                return False
            else:
                logging.info(f"✅ Сообщение отправлено пользователю {user_id}")
                self.log_message(user_id, "text", message, "outgoing")
                return True
                
        except Exception as e:
            logging.error(f"❌ Ошибка отправки сообщения: {e}")
            return False