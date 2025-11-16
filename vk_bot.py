import logging
import sqlite3
import json
import requests
import time
from datetime import datetime
from typing import Dict, Tuple, List

class VKBot:
    def __init__(self, token, db_path="dreams.db"):
        self.token = token
        self.db_path = db_path
        self.admin_ids = [822018853]
        self.free_requests_limit = 15
        
        # Инициализация компонентов
        self.init_database()
        
        logging.info("✅ VK Bot инициализирован!")

    def init_database(self):
        """Инициализация базы данных"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                requests_count INTEGER DEFAULT 0,
                is_subscribed BOOLEAN DEFAULT FALSE,
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
        
        self.conn.commit()
        logging.info("✅ База данных инициализирована!")

    def process_message(self, user_id: int, text: str, attachments: List[dict] = None) -> Tuple[str, dict]:
        """Обработка сообщения"""
        try:
            self.update_user_activity(user_id)
            is_admin = user_id in self.admin_ids
            
            # Обработка текстовых команд
            return self.process_text_message(user_id, text, is_admin)
            
        except Exception as e:
            logging.error(f"❌ Ошибка обработки сообщения: {e}")
            return "Произошла ошибка при обработке запроса", self.get_main_keyboard()

    def update_user_activity(self, user_id: int):
        """Обновление активности пользователя"""
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
        """Получение состояния пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT state FROM user_states WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else ""
        except Exception as e:
            logging.error(f"❌ Ошибка получения состояния: {e}")
            return ""

    def set_user_state(self, user_id: int, state: str, state_data: str = ""):
        """Установка состояния пользователя"""
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
        """Получение количества запросов пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT requests_count FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logging.error(f"❌ Ошибка получения количества запросов: {e}")
            return 0

    def increment_user_requests(self, user_id: int):
        """Увеличение счетчика запросов пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, requests_count, last_activity)
                VALUES (?, COALESCE((SELECT requests_count FROM users WHERE user_id = ?), 0) + 1, datetime('now'))
            ''', (user_id, user_id))
            self.conn.commit()
        except Exception as e:
            logging.error(f"❌ Ошибка увеличения счетчика запросов: {e}")

    def interpret_dream(self, user_id: int, dream_text: str) -> str:
        """Интерпретация сна"""
        try:
            from gigachat_api import gigachat
            
            interpretation = gigachat.interpret_dream(
                dream_text=dream_text,
                user_id=user_id,
                user_name="Пользователь"
            )
            
            return interpretation
            
        except Exception as e:
            logging.error(f"❌ Ошибка интерпретации сна: {e}")
            return f"""🔮 ПСИХОЛОГИЧЕСКАЯ ИНТЕРПРЕТАЦИЯ СНА

💭 **Ваш сон:** "{dream_text}"

🎭 **Базовый анализ:**
Сон содержит важные символы для анализа. Обратите внимание на основные образы и эмоции.

💫 **Рекомендации:**
- Записывайте сны регулярно
- Обращайте внимание на повторяющиеся темы
- Сравнивайте с предыдущими снами"""

    def process_text_message(self, user_id: int, text: str, is_admin: bool) -> Tuple[str, dict]:
        """Обработка текстового сообщения"""
        # Обработка отмены
        if text.lower() in ["отмена", "назад", "cancel", "❌ отмена"]:
            return self.handle_cancel(user_id)
        
        # Выход из админки
        if text.lower() in ["выйти из админки", "🔙 выйти из админки"]:
            self.set_user_state(user_id, "")
            return self.handle_default_response(user_id, is_admin)
        
        user_state = self.get_user_state(user_id)
        
        # Админские состояния
        if user_state.startswith("admin_") and is_admin:
            return self.handle_admin_state(user_id, text, user_state)
        
        # Основные команды
        if text.lower() in ["админка", "👑 админка"]:
            if is_admin:
                return self.handle_admin_panel(user_id)
            else:
                return "❌ У вас нет доступа к админ-панели", self.get_main_keyboard()
        
        if "интерпретировать сон" in text.lower() or "📖" in text:
            return self.handle_dream_interpretation_start(user_id, is_admin)
        
        if "история снов" in text.lower() or "📚" in text:
            return self.handle_user_dream_history(user_id)
        
        # Состояние ожидания сна
        if user_state == "waiting_for_dream":
            return self.handle_dream_text(user_id, text, is_admin)
        
        if "подписка" in text.lower() or "💎" in text:
            return self.handle_user_subscription(user_id, is_admin)
        
        return self.handle_default_response(user_id, is_admin)

    def handle_cancel(self, user_id: int) -> Tuple[str, dict]:
        """Обработка отмены"""
        try:
            self.set_user_state(user_id, "")
            return "Действие отменено. Возврат в главное меню.", self.get_main_keyboard()
        except Exception as e:
            logging.error(f"❌ Ошибка отмены: {e}")
            return "Возврат в главное меню.", self.get_main_keyboard()

    def handle_default_response(self, user_id: int, is_admin: bool) -> Tuple[str, dict]:
        """Стандартный ответ"""
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

    def handle_admin_panel(self, user_id: int) -> Tuple[str, dict]:
        """Админ-панель"""
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

    def get_admin_stats(self) -> Dict[str, int]:
        """Статистика для админа"""
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

    def handle_admin_state(self, user_id: int, text: str, state: str) -> Tuple[str, dict]:
        """Обработка админских состояний"""
        try:
            if state == "admin_view_users":
                if text.isdigit():
                    return self.handle_view_user_details(user_id, int(text))
                else:
                    return self.handle_admin_users_list(user_id)
            
            self.set_user_state(user_id, "")
            return self.handle_admin_panel(user_id)
            
        except Exception as e:
            logging.error(f"❌ Ошибка обработки состояния админа: {e}")
            self.set_user_state(user_id, "")
            return "Произошла ошибка", self.get_admin_keyboard()

    def handle_admin_users_list(self, user_id: int) -> Tuple[str, dict]:
        """Список пользователей"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
                SELECT user_id, username, requests_count, is_subscribed, last_activity
                FROM users 
                ORDER BY last_activity DESC
                LIMIT 20
            ''')
            
            users = cursor.fetchall()
            
            if not users:
                return "📝 Нет зарегистрированных пользователей.", self.get_admin_keyboard()
            
            users_text = "👥 ВСЕ ПОЛЬЗОВАТЕЛИ:\n\n"
            
            for user in users:
                user_id, username, requests_count, is_subscribed, last_activity = user
                status = "💎 ПОДПИСКА" if is_subscribed else "🔓 БЕСПЛАТНО"
                users_text += f"👤 ID: {user_id}\n"
                users_text += f"📛 Имя: {username or 'Не указано'}\n"
                users_text += f"📊 Запросов: {requests_count}\n"
                users_text += f"🎯 Статус: {status}\n"
                users_text += f"🕐 Активность: {last_activity[:16]}\n"
                users_text += "─" * 30 + "\n"
            
            users_text += "\n📝 Введите ID пользователя для подробной информации"
            
            self.set_user_state(user_id, "admin_view_users")
            return users_text, self.get_admin_users_keyboard()
            
        except Exception as e:
            logging.error(f"❌ Ошибка получения списка пользователей: {e}")
            return "❌ Ошибка при получении списка пользователей", self.get_admin_keyboard()

    def handle_view_user_details(self, user_id: int, target_user_id: int) -> Tuple[str, dict]:
        """Информация о пользователе"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
                SELECT user_id, username, requests_count, is_subscribed, last_activity, created_at
                FROM users WHERE user_id = ?
            ''', (target_user_id,))
            
            user_info = cursor.fetchone()
            
            if not user_info:
                return f"❌ Пользователь с ID {target_user_id} не найден.", self.get_admin_keyboard()
            
            user_id, username, requests_count, is_subscribed, last_activity, created_at = user_info
            
            cursor.execute("SELECT COUNT(*) FROM dreams WHERE user_id = ?", (target_user_id,))
            dreams_count = cursor.fetchone()[0]
            
            user_text = (
                f"👤 ПОДРОБНАЯ ИНФОРМАЦИЯ\n\n"
                f"🆔 ID: {user_id}\n"
                f"📛 Имя: {username or 'Не указано'}\n"
                f"📊 Запросов: {requests_count}\n"
                f"🔮 Снов: {dreams_count}\n"
                f"🎯 Статус: {'💎 ПОДПИСКА' if is_subscribed else '🔓 БЕСПЛАТНО'}\n"
                f"📅 Регистрация: {created_at[:16]}\n"
                f"🕐 Активность: {last_activity[:16]}\n"
            )
            
            return user_text, self.get_admin_back_keyboard()
            
        except Exception as e:
            logging.error(f"❌ Ошибка получения информации о пользователе: {e}")
            return "❌ Ошибка при получении информации о пользователе", self.get_admin_keyboard()

    def handle_dream_interpretation_start(self, user_id: int, is_admin: bool) -> Tuple[str, dict]:
        """Начало интерпретации сна"""
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
        """Обработка текста сна"""
        try:
            if not is_admin:
                self.increment_user_requests(user_id)
            
            interpretation = self.interpret_dream(user_id, text)
            
            # Сохраняем сон
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO dreams (user_id, dream_text, interpretation)
                VALUES (?, ?, ?)
            ''', (user_id, text, interpretation))
            self.conn.commit()
            
            self.set_user_state(user_id, "")
            
            return interpretation, self.get_main_keyboard()
            
        except Exception as e:
            logging.error(f"❌ Ошибка интерпретации сна: {e}")
            self.set_user_state(user_id, "")
            return "Произошла ошибка при интерпретации сна. Попробуйте еще раз.", self.get_main_keyboard()

    def handle_user_dream_history(self, user_id: int) -> Tuple[str, dict]:
        """История снов"""
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
        """Обработка подписки"""
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
                return subscription_text, self.get_subscription_keyboard()
        except Exception as e:
            logging.error(f"❌ Ошибка обработки подписки: {e}")
            return "❌ Ошибка при обработке подписки", self.get_main_keyboard()

    def show_subscription_offer(self, user_id: int, used_requests: int) -> Tuple[str, dict]:
        """Предложение подписки"""
        subscription_text = (
            f"🚫 БЕСПЛАТНЫЙ ЛИМИТ ИСЧЕРПАН\n\n"
            f"Вы использовали {used_requests} бесплатных интерпретаций снов.\n\n"
            f"💎 Для продолжения работы активируйте подписку:\n"
            f"Всего 299 руб/месяц за неограниченное количество анализов снов!\n\n"
            f"Напишите \"Подписка\" для активации"
        )
        return subscription_text, self.get_main_keyboard()

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

    def get_admin_keyboard(self):
        return {
            "inline": False,
            "buttons": [
                [{"action": {"type": "text", "label": "👥 Все пользователи"}, "color": "primary"}],
                [{"action": {"type": "text", "label": "📊 Статистика"}, "color": "secondary"}],
                [{"action": {"type": "text", "label": "🔙 Выйти из админки"}, "color": "negative"}]
            ]
        }

    def get_admin_users_keyboard(self):
        return {
            "inline": False,
            "buttons": [
                [{"action": {"type": "text", "label": "🔄 Обновить список"}, "color": "primary"}],
                [{"action": {"type": "text", "label": "🔙 Назад в админку"}, "color": "secondary"}]
            ]
        }

    def get_admin_back_keyboard(self):
        return {
            "inline": False,
            "buttons": [
                [{"action": {"type": "text", "label": "🔙 Назад к списку"}, "color": "secondary"}]
            ]
        }

    def get_cancel_keyboard(self):
        return {
            "inline": False,
            "buttons": [
                [{"action": {"type": "text", "label": "❌ Отмена"}, "color": "negative"}]
            ]
        }

    def get_subscription_keyboard(self):
        return {
            "inline": False,
            "buttons": [
                [{"action": {"type": "text", "label": "💳 Оплатить"}, "color": "positive"}],
                [{"action": {"type": "text", "label": "🔙 Назад"}, "color": "negative"}]
            ]
        }

    def send_message(self, user_id: int, message: str, keyboard: dict = None) -> bool:
        """Отправка сообщения"""
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
                return True
                
        except Exception as e:
            logging.error(f"❌ Ошибка отправки сообщения: {e}")
            return False