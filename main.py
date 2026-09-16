import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Крошечный HTTP-сервер для Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running", 200

# Твой бот
TOKEN = os.environ.get("TELEGRAM_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я твой покерный тренер. ♠️")

# Запуск бота в отдельном потоке
def run_bot():
    bot_app = ApplicationBuilder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    print("Bot is starting...")
    bot_app.run_polling()

if __name__ == '__main__':
    # Запускаем бота в фоне
    threading.Thread(target=run_bot, daemon=True).start()
    # Запускаем веб-сервер, чтобы Render был доволен
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
