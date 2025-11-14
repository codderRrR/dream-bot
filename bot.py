import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ТВОЙ ТОКЕН ОТ @BotFather
TELEGRAM_TOKEN = "8309048632:AAHAyHsfdvhjju6XxMYqwpwQ1oijKOA6EgY"
API_URL = "http://localhost:8000/interpret"

# 🔥 ХРАНИМ ПОСЛЕДНИЙ СОН ПОЛЬЗОВАТЕЛЯ
user_last_dreams = {}

async def start(update: Update, context):
    await update.message.reply_text(
        "🔮 *Добро пожаловать в ИИ Сонник!*\n\n"
        "Я помогу вам понять ваши сны с психологической точки зрения.\n\n"
        "✨ *Просто опишите свой сон, и я дам профессиональную интерпретацию*\n\n"
        "📖 *Доступные команды:*\n"
        "/history - посмотреть историю снов\n"
        "/help - помощь\n"
        "/site - ссылка на сайт\n\n"
        "💫 *После интерпретации можете уточнить:*\n"
        "• \"глубже\" - более детальный анализ\n"
        "• \"эмоции\" - анализ эмоций в сне\n" 
        "• \"символы\" - разбор символов\n"
        "• \"подробнее\" - расширенная интерпретация\n\n"
        "🌐 *Также доступно на сайте:*\n"
        "http://localhost:8000\n\n"
        "💫 *Пример:* \"Мне приснилось, что я летаю над городом...\"",
        parse_mode='Markdown'
    )

async def site(update: Update, context):
    await update.message.reply_text(
        "🌐 *Наш сайт с удобным чат-интерфейсом:*\n\n"
        "🔗 http://localhost:8000\n\n"
        "✨ *На сайте доступно:*\n"
        "• Красивый чат-интерфейс\n"
        "• Удобный ввод с клавиатуры\n"
        "• История диалога в реальном времени\n"
        "• Адаптивный дизайн\n\n"
        "💻 *Идеально для компьютера!*",
        parse_mode='Markdown'
    )

async def help(update: Update, context):
    await update.message.reply_text(
        "📖 *Доступные команды:*\n"
        "/start - начать работу\n" 
        "/history - посмотреть историю снов\n"
        "/site - получить ссылку на сайт\n"
        "/help - помощь\n\n"
        "💡 *Просто опишите свой сон для интерпретации!*\n\n"
        "💫 *После анализа можно уточнить:*\n"
        "• \"глубже\" - детальный анализ\n"
        "• \"эмоции\" - анализ чувств\n"
        "• \"символы\" - разбор символов\n" 
        "• \"подробнее\" - расширенная версия\n"
        "• \"что значит [символ]\" - разбор конкретного элемента\n\n"
        "✨ *Примеры:*\n"
        "• \"Мне снился летающий слон\"\n"
        "• После ответа: \"глубже\"\n"
        "• Или: \"какие эмоции я испытывал?\"",
        parse_mode='Markdown'
    )

async def history(update: Update, context):
    user = update.effective_user
    
    try:
        response = requests.get(f"http://localhost:8000/history/{user.id}")
        if response.status_code == 200:
            dreams = response.json()["dreams"]
            
            if not dreams:
                await update.message.reply_text("📝 У вас пока нет записанных снов.")
                return
            
            history_text = "📖 Ваша история снов:\n\n"
            for i, dream in enumerate(dreams[:5], 1):
                dream_text, interpretation, timestamp = dream
                history_text += f"{i}. **{dream_text[:50]}...**\n"
                history_text += f"   📅 {timestamp}\n\n"
            
            await update.message.reply_text(history_text)
        else:
            await update.message.reply_text("❌ Ошибка при получении истории")
            
    except Exception as e:
        await update.message.reply_text("❌ Произошла ошибка, попробуйте позже")

async def handle_dream(update: Update, context):
    dream_text = update.message.text
    user = update.effective_user
    
    # 🔥 ПРОВЕРЯЕМ, ЕСЛИ ЭТО УТОЧНЯЮЩИЙ ЗАПРОС ПРИ ОТСУТСТВИИ СОХРАНЕННОГО СНА
    if user.id not in user_last_dreams:
        # Если нет сохраненного сна, но пришли ключевые слова - просим описать сон
        message_text = dream_text.lower()
        if any(word in message_text for word in ["глубже", "подробнее", "эмоции", "символы", "что значит"]):
            await update.message.reply_text(
                "📝 Сначала опишите свой сон для анализа!\n"
                "Например: \"Мне приснилось, что я летаю над городом...\""
            )
            return
    
    try:
        response = requests.post(API_URL, json={
            "user_id": str(user.id),
            "dream_text": dream_text,
            "user_name": user.first_name or "Пользователь"
        })
        
        if response.status_code == 200:
            interpretation = response.json()["interpretation"]
            
            # 🔥 СОХРАНЯЕМ ПОСЛЕДНИЙ СОН ДЛЯ УТОЧНЕНИЙ
            user_last_dreams[user.id] = dream_text
            
            await update.message.reply_text(
                f"{interpretation}\n\n"
                "💫 *Хотите узнать больше? Напишите:*\n"
                "• \"глубже\" - детальный анализ\n"
                "• \"эмоции\" - анализ чувств\n" 
                "• \"символы\" - разбор символов\n"
                "• \"подробнее\" - расширенная версия",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Ошибка при обработке сна")
            
    except Exception as e:
        await update.message.reply_text("❌ Произошла ошибка, попробуйте позже")

# 🔥 ОБРАБОТКА УТОЧНЯЮЩИХ ВОПРОСОВ
async def handle_follow_up(update: Update, context):
    user = update.effective_user
    message_text = update.message.text.lower()
    
    # ПРОВЕРЯЕМ, ЕСТЬ ЛИ СОХРАНЕННЫЙ СОН
    if user.id not in user_last_dreams:
        # Если нет сохраненного сна - передаем обычному обработчику
        await handle_dream(update, context)
        return
    
    last_dream = user_last_dreams[user.id]
    
    # 🔥 ОПРЕДЕЛЯЕМ ТИП УТОЧНЕНИЯ
    is_follow_up = False
    enhanced_text = ""
    follow_up_type = ""
    
    if any(word in message_text for word in ["глубже", "подробнее", "детальнее", "разверни"]):
        is_follow_up = True
        follow_up_type = "глубокий анализ"
        enhanced_text = f"Дай максимально развернутый психологический анализ этого сна: {last_dream}. Рассмотри все аспекты и дай подробные рекомендации."
    
    elif any(word in message_text for word in ["эмоции", "чувства", "ощущения", "настроение"]):
        is_follow_up = True
        follow_up_type = "анализ эмоций" 
        enhanced_text = f"Проанализируй эмоциональную составляющую этого сна: {last_dream}. Какие эмоции преобладали? Что они могут значить в контексте жизни человека?"
    
    elif any(word in message_text for word in ["символы", "символика", "образы", "значение"]):
        is_follow_up = True
        follow_up_type = "анализ символов"
        enhanced_text = f"Разбери символику и образы этого сна: {last_dream}. Что могут означать ключевые символы с психологической точки зрения?"
    
    elif "что значит" in message_text or "значение" in message_text:
        is_follow_up = True
        follow_up_type = "разбор конкретного символа"
        symbol = message_text.replace("что значит", "").replace("значение", "").strip()
        enhanced_text = f"Проанализируй значение символа '{symbol}' в контексте этого сна: {last_dream}. Дай психологическую интерпретацию этого образа."
    
    # ЕСЛИ НЕ УТОЧНЯЮЩИЙ ЗАПРОС - ОБРАБАТЫВАЕМ КАК ОБЫЧНЫЙ СОН
    if not is_follow_up:
        await handle_dream(update, context)
        return
    
    try:
        # 🔥 ОТПРАВЛЯЕМ ЗАПРОС НА УГЛУБЛЕННЫЙ АНАЛИЗ
        response = requests.post(API_URL, json={
            "user_id": str(user.id),
            "dream_text": enhanced_text,
            "user_name": user.first_name or "Пользователь",
            "is_follow_up": True
        })
        
        if response.status_code == 200:
            interpretation = response.json()["interpretation"]
            
            await update.message.reply_text(
                f"💫 *{follow_up_type.title()}:*\n\n{interpretation}\n\n"
                "🔍 *Можете уточнить еще:*\n"
                "• Напишите другой вопрос о сне\n"
                "• Или опишите новый сон",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Ошибка при углубленном анализе")
            
    except Exception as e:
        await update.message.reply_text("❌ Произошла ошибка, попробуйте позже")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # РЕГИСТРИРУЕМ ОБРАБОТЧИКИ
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("site", site))
    
    # 🔥 ИСПРАВЛЕНИЕ: сначала уточнения, потом обычные сообщения
    # Уточнения имеют более высокий приоритет
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(r'(глубже|подробнее|эмоции|символы|что значит|значение)'), 
        handle_follow_up
    ))
    
    # Обычные сообщения (сны) - более низкий приоритет
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_dream))
    
    print("🤖 Telegram бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()