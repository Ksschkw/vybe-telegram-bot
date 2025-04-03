from telegram import Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
import os
import asyncio
from alerts_db import add_alert, get_user_alerts
from vybe_api import get_token_data, get_token_price

load_dotenv('../config/.env')
BOTAPIKEY = os.getenv("BOTAPIKEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **Vybe Alert Bot**\n\n"
        "Commands:\n"
        "/alert [token] [price] - Set price alert\n"
        "/checktoken [address] - Rug-pull risk score\n"
        "/myalerts - List your alerts\n\n"
        "🔧 Open Vybe Dashboard:",
        reply_markup={
            "inline_keyboard": [[{
                "text": "Open Dashboard",
                "web_app": {"url": "https://vybevigil.onrender.com/vybe-dashboard"}
            }]]
        }
    )

async def set_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        _, token, threshold = update.message.text.split()
        user_id = update.effective_user.id
        add_alert(user_id, token, float(threshold))
        await update.message.reply_text(f"✅ Alert set for {token} at ${threshold}")
        asyncio.create_task(monitor_prices(user_id, token, float(threshold)))
    except:
        await update.message.reply_text("❌ Format: /alert [TOKEN] [PRICE]")

async def check_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        _, token_address = update.message.text.split()
        data = get_token_data(token_address)
        risk_score = 50 if not data['liquidity_locked'] else 0
        risk_score += 30 if data['creator_owns'] > 20 else 0
        await update.message.reply_text(
            f"🕵️ **Risk Report**\n"
            f"Score: {risk_score}/100\n"
            f"Liquidity Locked: {'✅' if data['liquidity_locked'] else '❌'}\n"
            f"Creator Ownership: {data['creator_owns']}%"
        )
    except:
        await update.message.reply_text("❌ Invalid token address!")

async def monitor_prices(user_id, token, threshold):
    while True:
        price = get_token_price(token)
        if price >= threshold:
            await application.bot.send_message(
                chat_id=user_id,
                text=f"🚨 **{token} Alert!**\nCurrent Price: ${price}"
            )
            break
        await asyncio.sleep(60)

application = Application.builder().token(BOTAPIKEY).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("alert", set_alert))
application.add_handler(CommandHandler("checktoken", check_token))
application.run_polling()