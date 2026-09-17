import os
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- Flask ---
app = Flask(__name__)

# --- Telegram Bot ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot_app = ApplicationBuilder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я твой покерный тренер. ♠️")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я пока умею только здороваться. Скоро тут будет задача дня!")

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("help", help_command))

# --- Flask route, который принимает сообщения от Telegram ---
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    # Получаем данные от Telegram и передаём их в бота
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    bot_app.update_queue.put(update)
    return "ok", 200

@app.route('/')
def home():
    return "Bot is running", 200

# --- Инициализация бота и установка вебхука ---
if __name__ == '__main__':
    # Инициализируем бота (без запуска polling)
    bot_app.initialize()
    
    # Устанавливаем вебхук. URL берём из переменной окружения RENDER_EXTERNAL_URL
    # Render сам подставляет этот URL для твоего сервиса.
    external_url = os.environ.get("RENDER_EXTERNAL_URL")
    if external_url:
        webhook_url = f"{external_url}/{TOKEN}"
        bot_app.bot.set_webhook(url=webhook_url)
        print(f"Webhook set to {webhook_url}")
    
    # Запускаем Flask
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
