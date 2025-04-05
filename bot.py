from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import utils
import os
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
VYBE_API_KEY = os.getenv("VYBE_API_KEY")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Vybe Analytics Bot Activated!\n\n"
                               "Available commands:\n"
                               "/balance <wallet> - Check wallet balance\n"
                               "/prices <token> - Get token prices\n"
                               "/whalealert - Latest large transactions")

async def get_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet_address = context.args[0] if context.args else None
    if not wallet_address:
        await update.message.reply_text("Please provide a wallet address")
        return
    
    balance = await utils.get_wallet_balance(wallet_address)
    await update.message.reply_text(f"💰 Wallet Balance:\n{balance} SOL")

async def whale_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle whale alert command with optional threshold"""
    try:
        threshold = float(context.args[0]) if context.args else 1000
        alerts = await utils.detect_whale_transfers(threshold)
        await update.message.reply_text(
            f"🔔 Whale Transfers (> {threshold} SOL):\n\n{alerts}"
        )
    except ValueError:
        await update.message.reply_text("❌ Invalid threshold. Use /whalealert 500")

if __name__ == "__main__":
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", get_balance))
    app.add_handler(CommandHandler("whalealert", whale_alert))

    
    # Start polling
    app.run_polling()