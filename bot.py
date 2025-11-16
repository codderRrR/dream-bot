import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import sqlite3

TELEGRAM_TOKEN = "8309048632:AAHAyHsfdvhjju6XxMYqwpwQ1oijKOA6EgY"
API_URL = "http://localhost:8000/interpret"

user_last_dreams = {}

def get_user_dream_stats(user_id):
    """Получаем статистику снов пользователя"""
    try:
        conn = sqlite3.connect('dreams.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM dreams WHERE user_id = ?", (user_id,))
        total_dreams = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT dream_text, created_at FROM dreams 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 5
        ''', (user_id,))
        
        recent_dreams = cursor.fetchall()
        conn.close()
        
        return {
            'total_dreams': total_dreams,
            'recent_dreams': recent_dreams
        }
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")
        return {'total_dreams': 0, 'recent_dreams': []}

async def start(update: Update, context):
    user = update.effective_user
    stats = get_user_dream_stats(user.id)
    
    welcome_text = (
        f"🔮 *Добро пожаловать в продвинутый ИИ Сонник!*\n\n"
        f"✨ *Новые возможности:*\n"
        f"• 📊 Детальный анализ снов с психологической точки зрения\n"
        f"• 💭 Глубокий разбор эмоций и символов\n"
        f"• 🔍 Углубленные интерпретации по запросу\n"
        f"• 🌙 Учет истории ваших сновидений\n\n"
        f"💫 *Просто опишите свой сон, и вы получите развернутый анализ!*\n\n"
        f"*Пример:* \"Мне приснилось, что я летаю над городом...\""
    )
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def handle_dream(update: Update, context):
    dream_text = update.message.text
    user = update.effective_user
    
    # ПРОВЕРКА НА УТОЧНЯЮЩИЕ ЗАПРОСЫ БЕЗ СОХРАНЕННОГО СНА
    if user.id not in user_last_dreams:
        message_text = dream_text.lower()
        follow_up_keywords = ["подробнее", "эмоции", "символы", "динамика", "паттерны", "рекомендации", "детальнее", "глубже"]
        if any(word in message_text for word in follow_up_keywords):
            await update.message.reply_text(
                "📝 *Сначала опишите свой сон для анализа!*\n\n"
                "Например: \"Мне приснилось, что я летаю над городом...\"\n\n"
                "💫 После основного анализа вы сможете запросить углубленное изучение различных аспектов сна.",
                parse_mode='Markdown'
            )
            return
    
    try:
        response = requests.post(API_URL, json={
            "user_id": str(user.id),
            "dream_text": dream_text,
            "user_name": user.first_name or "Пользователь",
            "is_follow_up": False
        })
        
        if response.status_code == 200:
            interpretation = response.json()["interpretation"]
            
            # СОХРАНЯЕМ ПОСЛЕДНИЙ СОН ДЛЯ УТОЧНЕНИЙ
            user_last_dreams[user.id] = dream_text
            
            await update.message.reply_text(
                interpretation,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Ошибка при обработке сна")
            
    except Exception as e:
        await update.message.reply_text("❌ Произошла ошибка, попробуйте позже")

async def handle_follow_up(update: Update, context):
    user = update.effective_user
    message_text = update.message.text.lower()
    
    if user.id not in user_last_dreams:
        await handle_dream(update, context)
        return
    
    last_dream = user_last_dreams[user.id]
    stats = get_user_dream_stats(user.id)
    
    is_follow_up = False
    follow_up_type = ""
    
    # ОПРЕДЕЛЯЕМ ТИП УГЛУБЛЕННОГО АНАЛИЗА
    if any(word in message_text for word in ["подробнее", "детальнее", "глубже", "📊"]):
        is_follow_up = True
        follow_up_type = "детальный анализ"
    
    elif any(word in message_text for word in ["эмоции", "эмоциональный", "чувства", "💭"]):
        is_follow_up = True
        follow_up_type = "анализ эмоций"
    
    elif any(word in message_text for word in ["символы", "символика", "образы", "🔍"]):
        is_follow_up = True
        follow_up_type = "анализ символов"
    
    elif any(word in message_text for word in ["динамика", "сравнение", "история", "🌙"]):
        is_follow_up = True
        follow_up_type = "анализ динамики"
    
    elif any(word in message_text for word in ["паттерны", "повторения", "темы", "🎯"]):
        is_follow_up = True
        follow_up_type = "анализ паттернов"
    
    elif any(word in message_text for word in ["рекомендации", "советы", "что делать", "🌟"]):
        is_follow_up = True
        follow_up_type = "практические рекомендации"
    
    if not is_follow_up:
        await handle_dream(update, context)
        return
    
    try:
        response = requests.post(API_URL, json={
            "user_id": str(user.id),
            "dream_text": last_dream,
            "user_name": user.first_name or "Пользователь",
            "is_follow_up": True
        })
        
        if response.status_code == 200:
            interpretation = response.json()["interpretation"]
            
            await update.message.reply_text(
                f"💫 *{follow_up_type.upper()}*\n\n{interpretation}\n\n"
                f"📚 *Изучите другие аспекты сна:*\n"
                f"• Напишите другой тип анализа\n"
                f"• Или опишите новый сон",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Ошибка при углубленном анализе")
            
    except Exception as e:
        await update.message.reply_text("❌ Произошла ошибка, попробуйте позже")

# ОСТАЛЬНЫЕ ФУНКЦИИ ОСТАЮТСЯ ПРЕЖНИМИ
async def history(update: Update, context):
    user = update.effective_user
    stats = get_user_dream_stats(user.id)
    
    if stats['total_dreams'] == 0:
        await update.message.reply_text(
            "📝 У вас пока нет записанных снов. Начните с интерпретации первого сна!",
            parse_mode='Markdown'
        )
        return
    
    history_text = f"📚 *ВАША ИСТОРИЯ СНОВИДЕНИЙ*\n\n"
    history_text += f"📊 Всего проанализировано: {stats['total_dreams']} снов\n\n"
    
    if stats['recent_dreams']:
        history_text += "🕐 *Последние сны:*\n"
        for i, (dream_text, created_at) in enumerate(stats['recent_dreams'], 1):
            date_str = created_at[:16] if created_at else "Неизвестно"
            history_text += f"{i}. {dream_text[:80]}...\n"
            history_text += f"   📅 {date_str}\n\n"
    
    history_text += (
        "💡 *После описания сна можете запросить:*\n"
        "• \"📊 Подробнее\" - детальный анализ\n"
        "• \"💭 Эмоции\" - разбор чувств\n"
        "• \"🔍 Символы\" - анализ образов\n"
        "• \"🌙 Динамика\" - сравнение с историей\n"
        "• \"🎯 Паттерны\" - повторяющиеся темы\n"
        "• \"🌟 Рекомендации\" - практические советы"
    )
    
    await update.message.reply_text(history_text, parse_mode='Markdown')

async def site(update: Update, context):
    await update.message.reply_text(
        "🌐 *Наш сайт с удобным чат-интерфейсом:*\n\n"
        "🔗 http://localhost:8000\n\n"
        "✨ *Расширенные возможности на сайте:*\n"
        "• Визуализация динамики снов\n"
        "• Детальная статистика анализа\n"
        "• Архив всех интерпретаций\n"
        "• Углубленные отчеты\n\n"
        "💻 *Идеально для комплексного анализа!*",
        parse_mode='Markdown'
    )

async def help(update: Update, context):
    help_text = (
        "📖 *ПРОДВИНУТЫЙ АНАЛИЗ СНОВИДЕНИЙ*\n\n"
        "🎯 *Как работает система:*\n"
        "1. Опишите свой сон\n"
        "2. Получите развернутую психологическую интерпретацию\n"
        "3. Запросите углубленный анализ нужных аспектов\n\n"
        "💫 *Команды углубленного анализа (после описания сна):*\n"
        "• \"📊 Подробнее\" - детальный разбор всех аспектов\n"
        "• \"💭 Эмоции\" - глубокий анализ чувств и переживаний\n"
        "• \"🔍 Символы\" - разбор ключевых образов и их значения\n"
        "• \"🌙 Динамика\" - сравнение с историей ваших снов\n"
        "• \"🎯 Паттерны\" - выявление повторяющихся тем\n"
        "• \"🌟 Рекомендации\" - практические советы для работы\n\n"
        "🔮 *Просто опишите сон и исследуйте его глубины!*"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("site", site))
    
    # ОБНОВЛЕННЫЙ ОБРАБОТЧИК УГЛУБЛЕННЫХ ЗАПРОСОВ
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(
            r'(?i)(подробнее|детальнее|глубже|эмоции|символы|динамика|паттерны|рекомендации|📊|💭|🔍|🌙|🎯|🌟)'
        ), 
        handle_follow_up
    ))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_dream))
    
    print("🤖 Продвинутый Telegram бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()