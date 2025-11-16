

import sqlite3
import os
import time

def rebuild_database():
    print("🗄️ Пересоздаем базу данных...")
    
    db_file = 'dreams.db'
    
    # Пробуем удалить старую базу с повторными попытками
    max_retries = 5
    for attempt in range(max_retries):
        try:
            if os.path.exists(db_file):
                os.remove(db_file)
                print("✅ Старая база удалена")
                break
            else:
                print("✅ Старой базы не существует")
                break
        except PermissionError:
            if attempt < max_retries - 1:
                print(f"🔄 Попытка {attempt + 1}/{max_retries}: Файл занят, ждем...")
                time.sleep(2)
            else:
                print("🚨 Не удалось удалить файл! Продолжаем с существующей базой...")
                # Не прерываем выполнение, продолжаем с существующей базой
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # СОЗДАЕМ ТАБЛИЦЫ С IF NOT EXISTS (на всякий случай)
    print("📊 Создаем таблицы...")
    
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
            is_voice BOOLEAN DEFAULT FALSE,
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
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS error_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            error_type TEXT,
            error_message TEXT,
            stack_trace TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
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
    
    conn.commit()
    
    # ДОБАВЛЯЕМ ТЕСТОВЫЕ ДАННЫЕ
    print("🧪 Добавляем тестовые данные...")
    
    # Админ пользователь
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, requests_count, is_subscribed)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (822018853, "admin_user", "Admin", "User", 5, True))
    
    # Тестовые пользователи
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, requests_count)
        VALUES (?, ?, ?, ?, ?)
    ''', (123456789, "test_user1", "Иван", "Петров", 2))
    
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, requests_count, is_subscribed)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (987654321, "premium_user", "Мария", "Сидорова", 15, True))
    
    
    # Тестовые сны
    cursor.execute('''
        INSERT OR IGNORE INTO dreams (user_id, dream_text, interpretation, is_voice)
        VALUES (?, ?, ?, ?)
    ''', (
        822018853, 
        "Приснилось что я летал над городом и видел все улицы с высоты", 
        "🔮 **ПСИХОЛОГИЧЕСКАЯ ИНТЕРПРЕТАЦИЯ СНА**\n\nСон о полете над городом символизирует ваше стремление к свободе и обзору жизненных ситуаций. Вы, вероятно, ищете новые перспективы или хотите выйти за рамки текущих ограничений.", 
        False
    ))
    
    cursor.execute('''
        INSERT OR IGNORE INTO dreams (user_id, dream_text, interpretation, is_voice)
        VALUES (?, ?, ?, ?)
    ''', (
        123456789, 
        "Снился экзамен в университете, я не был готов", 
        "🔮 **ПСИХОЛОГИЧЕСКАЯ ИНТЕРПРЕТАЦИЯ СНА**\n\nСон об экзамене часто отражает беспокойство по поводу оценки ваших способностей в реальной жизни. Возможно, вы чувствуете себя неподготовленным к важному событию или решению.", 
        True
    ))
    
    # Тестовые логи
    cursor.execute('''
        INSERT OR IGNORE INTO message_logs (user_id, message_type, message_text, direction)
        VALUES (?, ?, ?, ?)
    ''', (822018853, "text", "привет", "incoming"))
    
    cursor.execute('''
        INSERT OR IGNORE INTO message_logs (user_id, message_type, message_text, direction)
        VALUES (?, ?, ?, ?)
    ''', (822018853, "text", "Добро пожаловать!", "outgoing"))

    cursor.execute('''
    INSERT OR IGNORE INTO message_logs (user_id, message_type, message_text, direction)
    VALUES (?, ?, ?, ?)
''', (822018853, "text", "привет", "incoming"))

    cursor.execute('''
    INSERT OR IGNORE INTO message_logs (user_id, message_type, message_text, direction)
    VALUES (?, ?, ?, ?)
''', (822018853, "text", "Добро пожаловать!", "outgoing"))

    cursor.execute('''
    INSERT OR IGNORE INTO error_logs (user_id, error_type, error_message)
    VALUES (?, ?, ?)
''', (822018853, "DatabaseError", "Ошибка подключения к базе данных"))

    cursor.execute('''
    INSERT OR IGNORE INTO admin_actions (admin_id, action_type, target_user_id, details)
    VALUES (?, ?, ?, ?)
''', (822018853, "user_search", 123456789, "Поиск пользователя по ID"))
    
    conn.commit()
    
    # ПРОВЕРЯЕМ ЧТО ВСЕ СОЗДАЛОСЬ
    print("🔍 Проверяем созданные таблицы...")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("✅ Созданные таблицы:")
    for table in tables:
        print(f"   📊 {table[0]}")
    
    # СТАТИСТИКА
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM dreams")
    dreams_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM message_logs")
    logs_count = cursor.fetchone()[0]
    
    print(f"\n📈 Статистика базы:")
    print(f"   👥 Пользователей: {user_count}")
    print(f"   🔮 Снов: {dreams_count}")
    print(f"   📨 Логов сообщений: {logs_count}")
    
    conn.close()
    
    print(f"\n🎉 База данных успешно создана: {db_file}")
    return db_file

def test_database_connection():
    """Тестируем подключение к базе"""
    print("\n🔧 Тестируем подключение к базе...")
    
    try:
        conn = sqlite3.connect('dreams.db')
        cursor = conn.cursor()
        
        # Простой запрос
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        if result and result[0] == 1:
            print("✅ Подключение к базе работает корректно")
        else:
            print("❌ Проблема с подключением к базе")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к базе: {e}")
        return False

if __name__ == "__main__":
    print("🚀 ЗАПУСК ПЕРЕСОЗДАНИЯ БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    # Останавливаем все процессы вручную
    print("⚠️  Убедитесь, что бот остановлен (Ctrl+C в окне запуска)")
    input("Нажмите Enter чтобы продолжить...")
    
    new_db = rebuild_database()
    test_database_connection()
    
    print("\n" + "=" * 50)
    print("🎉 БАЗА ДАННЫХ ГОТОВА К ИСПОЛЬЗОВАНИЮ!")
    print("\n📝 Дальнейшие действия:")
    print("1. 🚀 Запустите бота: python main.py")
    print("2. 🔧 Протестируйте голосовые сообщения")
    print("3. 👑 Проверьте админ-панель")