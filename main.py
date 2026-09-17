import os
import asyncio
import threading
import random
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- Flask ---
app = Flask(__name__)

# --- Telegram Bot ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot_app = ApplicationBuilder().token(TOKEN).build()

# --- База задач ---
TASKS = [
    {
        "id": 1,
        "situation": "Ты на баттоне. Все сфолдили до тебя. У тебя A♠K♠. Твоё действие?",
        "options": ["Рейз", "Колл", "Фолд"],
        "correct": "Рейз",
        "explanation": "AKs — премиум-рука. На баттоне ты должен рейзить, чтобы забирать блайнды и играть в позиции."
    },
    {
        "id": 2,
        "situation": "Ты на большом блайнде. У тебя 7♦2♣. UTG рейзит. Твоё действие?",
        "options": ["Рейз", "Колл", "Фолд"],
        "correct": "Фолд",
        "explanation": "72o — худшая рука в покере. Никогда не играй её против рейза, особенно без позиции."
    },
    {
        "id": 3,
        "situation": "Ты на катоффе. У тебя Q♥Q♦. Все сфолдили. Твоё действие?",
        "options": ["Рейз", "Колл", "Фолд"],
        "correct": "Рейз",
        "explanation": "QQ — очень сильная рука. Ты должна рейзить, чтобы изолировать и забирать деньги у слабых рук."
    },
    {
        "id": 4,
        "situation": "Ты на малом блайнде. У тебя J♠T♠. Все сфолдили до тебя. Твоё действие?",
        "options": ["Рейз", "Колл", "Фолд"],
        "correct": "Рейз",
        "explanation": "JTs — хорошая рука для стила. На малом блайнде лучше рейзить, чтобы забирать блайнд большого блайнда."
    },
    {
        "id": 5,
        "situation": "Ты на баттоне. У тебя 5♥5♦. UTG рейзит, все сфолдили. Твоё действие?",
        "options": ["Рейз", "Колл", "Фолд"],
        "correct": "Колл",
        "explanation": "Мелкие пары хороши для сет-майнинга. Ты можешь коллировать в позиции, чтобы поймать сет на флопе."
    },
]

# --- Счёт пользователей (в памяти; при перезапуске сбросится) ---
USER_SCORES = {}

# --- Вспомогательные функции ---
def get_task_by_id(task_id):
    for task in TASKS:
        if task["id"] == task_id:
            return task
    return None

def get_random_task():
    return random.choice(TASKS)

# --- Команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in USER_SCORES:
        USER_SCORES[user_id] = {"correct": 0, "total": 0}
    
    await update.message.reply_text(
        "Привет! Я твой покерный тренер. ♠️\n"
        "Напиши /task, чтобы получить задачу дня.\n"
        "Напиши /score, чтобы посмотреть свой счёт."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Я умею:\n"
        "/task — случайная задача\n"
        "/score — твой счёт\n"
        "/start — начать сначала"
    )

async def score_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    score = USER_SCORES.get(user_id, {"correct": 0, "total": 0})
    await update.message.reply_text(
        f"📊 Твой счёт:\n"
        f"Правильных: {score['correct']}\n"
        f"Всего: {score['total']}"
    )

async def task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task = get_random_task()
    
    keyboard = [
        [InlineKeyboardButton(opt, callback_data=f"answer|{task['id']}|{opt}")] for opt in task["options"]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎯 Задача:\n\n{task['situation']}",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Разбираем callback_data: "answer|id|Рейз"
    data = query.data.split("|")
    if len(data) != 3:
        return
    
    task_id = int(data[1])
    user_answer = data[2]
    task = get_task_by_id(task_id)
    
    if not task:
        await query.edit_message_text("Ошибка: задача не найдена.")
        return
    
    user_id = query.from_user.id
    if user_id not in USER_SCORES:
        USER_SCORES[user_id] = {"correct": 0, "total": 0}
    USER_SCORES[user_id]["total"] += 1
    
    if user_answer == task["correct"]:
        USER_SCORES[user_id]["correct"] += 1
        result = f"✅ Правильно! Ты выбрал {user_answer}.\n\n"
    else:
        result = f"❌ Неправильно. Правильный ответ: {task['correct']}.\n\n"
    
    result += f"💡 {task['explanation']}"
    
    await query.edit_message_text(text=result)

# --- Регистрируем обработчики ---
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("help", help_command))
bot_app.add_handler(CommandHandler("task", task_command))
bot_app.add_handler(CommandHandler("score", score_command))
bot_app.add_handler(CallbackQueryHandler(button_handler))

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

threading.Thread(target=run_bot_loop, daemon=True).start()

# --- Flask ---
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
