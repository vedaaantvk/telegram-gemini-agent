import os
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    CommandHandler, MessageHandler, filters
)

# 🔐 Replace with your actual keys
TELEGRAM_TOKEN = "8263999156:AAGKHwcwFxsRZ_ejOdmBvF1s8yQH4MwqSic"
GEMINI_API_KEY = "AIzaSyATmp-9xSmrbn02NeF__aL96JwsrG5diYI"

app = Flask(__name__)
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# --- Gemini Prompt Builder ---
def build_prompt(goal, days):
    return {
        "contents": [{
            "parts": [{
                "text": f"""
You are a realistic, detail-obsessed project planner.

Goal: {goal}
Days Available: {days}

Instructions:
- Break it into clear phases.
- Give daily tasks, milestones, tools needed.
- Be honest: add warnings, tips, and realistic expectations.
- Deliver JSON with goal, days, and daily plan.
"""
            }]
        }]
    }

# --- Gemini API Request ---
def get_plan_from_gemini(goal, days):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    payload = build_prompt(goal, days)
    response = requests.post(url, json=payload)
    data = response.json()
    try:
        return data['candidates'][0]['content']['parts'][0]['text']
    except:
        return "⚠️ Error: Couldn't get a valid response from Gemini."

# --- Telegram Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hi! Send me your goal like this:\n\nGoal: Learn Python\nDays: 14")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "goal" in text.lower() and "days" in text.lower():
        try:
            goal = text.split("goal:")[1].split("days:")[0].strip()
            days = int(text.lower().split("days:")[1].strip())
            await update.message.reply_text("⏳ Generating your plan...")
            plan = get_plan_from_gemini(goal, days)
            await update.message.reply_text(plan[:4096])
        except Exception as e:
            await update.message.reply_text("❌ Please format your message like:\nGoal: ...\nDays: ...")
    else:
        await update.message.reply_text("❌ Please format your message like:\nGoal: ...\nDays: ...")

# --- Add Handlers ---
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route("/")
def index():
    return "Bot is running."

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return 'ok'

# --- Run Flask App ---
if __name__ == "__main__":
    import asyncio

    async def run_bot():
        await application.initialize()
        await application.start()
        print("Bot polling initialized (webhook will be used via Flask).")
        await application.updater.start_polling()  # Optional fallback

    loop = asyncio.get_event_loop()
    loop.create_task(run_bot())
    app.run(port=8443)
