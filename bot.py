from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
)
import requests
import datetime
import os

# --- Bot Token Environment Variable থেকে নেবে ---
BOT_TOKEN = os.getenv("BOT_TOKEN")


# --- API কল করার ফাংশন ---
def sowrov_stats(api_key, day="today", date_from=None, date_to=None):
    if day == "today":
        date_from = date_to = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    elif day == "yesterday":
        date_from = date_to = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).strftime(
            "%Y-%m-%d")
    elif date_from and date_to:
        date_from = date_from.strftime("%Y-%m-%d")
        date_to = date_to.strftime("%Y-%m-%d")
    else:
        date_from = date_to = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    url = "https://api.monetag.com/v5/pub/statistics"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"group_by": ["site_id"], "date_from": date_from, "date_to": date_to, "page": 1, "page_size": 100}

    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        impressions = revenue = cpm = 0
        for row in data.get("result", []):
            impressions += int(row.get("impressions", 0))
            revenue += float(row.get("money", 0))
        if impressions > 0:
            cpm = revenue / impressions * 1000
        return impressions, revenue, cpm
    except Exception as e:
        print("Stats Error:", e)
        return 0, 0, 0


# --- Reply Keyboard ---
def get_main_reply_keyboard():
    keyboard = [
        ["📊 Today Stats", "📅 Yesterday Stats"],
        ["📈 Weekly Stats", "🗓 This Year Stats"],
        ["✨ Custom Date Range", "🚪 Logout"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


# --- Start Handler ---
async def sowrov_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_tokens = context.bot_data.get('user_tokens', {})
    if user_id not in user_tokens:
        await update.message.reply_text("🔑 Please send your Monetag API Token:", reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text("✅ Welcome back!\nChoose an option:", reply_markup=get_main_reply_keyboard())


# --- Message Handler ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    state = context.user_data.get('state')

    user_tokens = context.bot_data.setdefault('user_tokens', {})

    # Step 1: API Token Save
    if user_id not in user_tokens:
        user_tokens[user_id] = text
        await update.message.reply_text("✅ API Token Saved!\nNow choose an option:",
                                        reply_markup=get_main_reply_keyboard())
        return

    api_key = user_tokens[user_id]

    # --- Example Command: Today Stats ---
    if text == "📊 Today Stats":
        impressions, revenue, cpm = sowrov_stats(api_key, "today")
        msg = f"📊 Today's Report\n\n👁 Impressions: {impressions}\n💵 Profit: ${round(revenue, 3)}\n📈 CPM: ${round(cpm, 2)}"
        await update.message.reply_text(text=msg, reply_markup=get_main_reply_keyboard())
    else:
        await update.message.reply_text("Please choose a valid option from the keyboard.",
                                        reply_markup=get_main_reply_keyboard())


if __name__ == "__main__":
    if not BOT_TOKEN:
        raise ValueError("Error: BOT_TOKEN is not set.")

    # ❌ আর Persistence নেই
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", sowrov_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running fresh every time... 🚀")
    app.run_polling()
