import os
import asyncio
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
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    # Передаём сообщение в очередь бота
    asyncio.run_coroutine_threadsafe(
        bot_app.update_queue.put(update),
        bot_app.loop
    )
    return "ok", 200

@app.route('/')
def home():
    return "Bot is running", 200

# --- Инициализация бота и установка вебхука ---
async def setup_bot():
    await bot_app.initialize()
    await bot_app.start()
    
    external_url = os.environ.get("RENDER_EXTERNAL_URL")
    if external_url:
        webhook_url = f"{external_url}/{TOKEN}"
        await bot_app.bot.set_webhook(url=webhook_url)
        print(f"Webhook set to {webhook_url}")

if __name__ == '__main__':
    # Запускаем инициализацию бота в фоне
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bot_app.loop = loop
    loop.run_until_complete(setup_bot())
    
    # Запускаем Flask в главном потоке
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
