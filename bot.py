import os
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes,
    CommandHandler, MessageHandler, filters
)

# --- Set your tokens securely ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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

def get_plan_from_gemini(goal, days):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    payload = build_prompt(goal, days)
    try:
        res = requests.post(url, json=payload)
        data = res.json()
        return data['candidates'][0]['content']['parts'][0]['text']
    except:
        return "⚠️ Error: Couldn't get a valid response from Gemini."

# --- Flask + Telegram App ---
app = Flask(__name__)
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# Telegram handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me your goal like this:\n\nGoal: Learn Python\nDays: 14")

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
            await update.message.reply_text("❌ Please format like:\nGoal: ...\nDays: ...")
    else:
        await update.message.reply_text("❌ Please format like:\nGoal: ...\nDays: ...")

# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route("/")
def root():
    return "Bot is live."

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

# Startup
if __name__ == "__main__":
    import asyncio

    async def run():
        await application.initialize()
        await application.start()
        await application.bot.set_webhook(url=f"https://goalpilot.onrender.com/{TELEGRAM_TOKEN}")
        print("✅ Webhook set and bot is running.")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    app.run(host="0.0.0.0", port=10000)
