import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, BotCommand
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import json
import os
from datetime import datetime, timedelta
import threading

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load or initialize data storage
DATA_FILE = "posts.json"
posts = {}  # Structure: {chat_id: {"drafts": [...], "scheduled": [...]}}
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as file:
        posts = json.load(file)

def save_data():
    with open(DATA_FILE, "w") as file:
        json.dump(posts, file, indent=4)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome! Use /newpost to create a post.")

def new_post(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)
    if chat_id not in posts:
        posts[chat_id] = {"drafts": [], "scheduled": []}
    posts[chat_id]["drafts"].append({"text": "", "buttons": [], "timestamp": None})
    save_data()
    update.message.reply_text("New draft created! Use /editpost to modify it.")

def edit_post(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)
    if chat_id not in posts or not posts[chat_id]["drafts"]:
        update.message.reply_text("No drafts available.")
        return
    posts[chat_id]["drafts"][-1]["text"] = " ".join(context.args)
    save_data()
    update.message.reply_text("Post updated! Use /schedule to schedule or /publish to send.")

def schedule_post(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)
    if chat_id not in posts or not posts[chat_id]["drafts"]:
        update.message.reply_text("No drafts available.")
        return
    try:
        delay = int(context.args[0])  # Delay in minutes
        timestamp = (datetime.now() + timedelta(minutes=delay)).timestamp()
        posts[chat_id]["drafts"][-1]["timestamp"] = timestamp
        posts[chat_id]["scheduled"].append(posts[chat_id]["drafts"].pop())
        save_data()
        update.message.reply_text(f"Post scheduled in {delay} minutes!")
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /schedule <minutes>")

def publish_post(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat_id)
    if chat_id not in posts or not posts[chat_id]["drafts"]:
        update.message.reply_text("No drafts available.")
        return
    post = posts[chat_id]["drafts"].pop()
    save_data()
    update.message.reply_text(post["text"], reply_markup=InlineKeyboardMarkup(post["buttons"]))

def check_scheduled():
    while True:
        now = datetime.now().timestamp()
        for chat_id, data in posts.items():
            for post in data["scheduled"][:]:
                if post["timestamp"] <= now:
                    context.bot.send_message(chat_id, post["text"], reply_markup=InlineKeyboardMarkup(post["buttons"]))
                    data["scheduled"].remove(post)
        save_data()
        time.sleep(60)

if __name__ == "__main__":
    from dotenv import load_dotenv
    import time

    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("newpost", new_post))
    dp.add_handler(CommandHandler("editpost", edit_post, pass_args=True))
    dp.add_handler(CommandHandler("schedule", schedule_post, pass_args=True))
    dp.add_handler(CommandHandler("publish", publish_post))
    
    threading.Thread(target=check_scheduled, daemon=True).start()
    
    updater.start_polling()
    updater.idle()

# requirements.txt
# python-telegram-bot==13.15
# python-dotenv==1.0.0

# Dockerfile
# FROM python:3.9
# WORKDIR /bot
# COPY . /bot
# RUN pip install -r requirements.txt
# CMD ["python", "main.py"]

# README.md
# # Telegram Post Bot
# This bot allows admins to create, schedule, and publish posts with buttons.
# ## Setup
# - Add your Telegram bot token in a `.env` file as `BOT_TOKEN=your_token_here`
# - Run `docker build -t telegram-post-bot .`
# - Deploy to Koyeb with `docker run -d telegram-post-bot`
