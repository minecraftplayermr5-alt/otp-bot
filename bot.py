import os
import random
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TOKEN_HERE")

otp_store = {}  # {user_id: {"code": str, "expires": datetime, "attempts": int}}

OTP_LENGTH = 6
OTP_TTL_SECONDS = 120
MAX_ATTEMPTS = 3


def generate_otp():
    return str(random.randint(10 ** (OTP_LENGTH - 1), 10 ** OTP_LENGTH - 1))


def cleanup_expired():
    now = datetime.now()
    for uid in list(otp_store.keys()):
        if otp_store[uid]["expires"] < now:
            del otp_store[uid]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 OTP Bot-এ স্বাগতম!\n"
        "/generate — নতুন OTP নিন\n"
        "OTP টা ২ মিনিটে এক্সপায়ার হবে।"
    )


async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cleanup_expired()
    uid = update.effective_user.id
    code = generate_otp()
    otp_store[uid] = {
        "code": code,
        "expires": datetime.now() + timedelta(seconds=OTP_TTL_SECONDS),
        "attempts": 0,
    }
    await update.message.reply_text(
        f"✅ আপনার OTP: `{code}`\n"
        f"⏱️ মেয়াদ: {OTP_TTL_SECONDS} সেকেন্ড\n"
        f"📨 কোডটা লিখে পাঠান ভেরিফাই করতে।",
        parse_mode="Markdown",
    )


async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    if uid not in otp_store:
        await update.message.reply_text("❌ আগে /generate দিয়ে OTP নিন।")
        return

    data = otp_store[uid]

    if datetime.now() > data["expires"]:
        del otp_store[uid]
        await update.message.reply_text("⏰ OTP এক্সপায়ার হয়ে গেছে। আবার /generate করুন।")
        return

    if data["attempts"] >= MAX_ATTEMPTS:
        del otp_store[uid]
        await update.message.reply_text("🚫 অনেকবার ভুল। নতুন OTP নিন।")
        return

    if text == data["code"]:
        del otp_store[uid]
        await update.message.reply_text("🎉 OTP সঠিক! ভেরিফিকেশন সফল।")
    else:
        data["attempts"] += 1
        left = MAX_ATTEMPTS - data["attempts"]
        await update.message.reply_text(f"❌ ভুল OTP। বাকি চেষ্টা: {left}")


def main():
    if BOT_TOKEN == "YOUR_TOKEN_HERE":
        print("⚠️ BOT_TOKEN সেট করুন! Render-এ Environment Variable হিসেবে বসান।")
        return

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate", generate))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, verify))

    print("🤖 Bot চলছে...")
    app.run_polling()


if __name__ == "__main__":
    main()