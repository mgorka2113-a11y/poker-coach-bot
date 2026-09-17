import os
import asyncio
import threading
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

# --- Глобальный цикл событий ---
loop = asyncio.new_event_loop()

async def setup_bot():
    await bot_app.initialize()
    await bot_app.start()
    external_url = os.environ.get("RENDER_EXTERNAL_URL")
    if external_url:
        webhook_url = f"{external_url}/{TOKEN}"
        await bot_app.bot.set_webhook(url=webhook_url)
        print(f"Webhook set to {webhook_url}")

def run_bot_loop():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup_bot())
    loop.run_forever()

# Запускаем цикл событий бота в отдельном потоке
threading.Thread(target=run_bot_loop, daemon=True).start()

# --- Flask route, который принимает сообщения от Telegram ---
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    asyncio.run_coroutine_threadsafe(bot_app.update_queue.put(update), loop)
    return "ok", 200

@app.route('/')
def home():
    return "Bot is running", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
