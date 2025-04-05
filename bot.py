import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext
import requests
import json
from dotenv import load_dotenv

load_dotenv()


# Config
TELEGRAM_TOKEN =  os.getenv("TELEGRAM_TOKEN")
VYBE_API_KEY=  os.getenv("VYBE_API_KEY")
VYBE_API_URL = "https://api.vybenetwork.xyz/account/known-accounts"

# Start Command
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "🚀 Vybe Bot Activated!\n"
        "Commands:\n"
        "/portfolio [wallet_address] - Check holdings\n"
        "/whalealert - Set alerts\n"
        "/gas - Solana gas prices\n"
        "/help - Assistance"
    )

# Portfolio Command (Vybe API: Balances)
async def portfolio(update: Update, context: CallbackContext) -> None:
    wallet_address = context.args[0] if context.args else None
    if not wallet_address:
        await update.message.reply_text("❌ Missing wallet address! Example: /portfolio 8x3D...")
        return
    
    headers = {'X-API-Key': VYBE_API_KEY}
    response = requests.get(f"{VYBE_API_URL}/balances/{wallet_address}", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        # Format response (we’ll refine this later)
        await update.message.reply_text(f"📊 Portfolio:\n{json.dumps(data, indent=2)}")
    else:
        await update.message.reply_text("⚠️ API Error! Try again later.")

# Gas Command (Vybe API: Gas Prices)
async def gas(update: Update, context: CallbackContext) -> None:
    headers = {'X-API-Key': VYBE_API_KEY}
    response = requests.get(f"{VYBE_API_URL}/gas", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        gas_price = data.get('current', 'N/A')
        await update.message.reply_text(f"⛽ Solana Gas Price: {gas_price} SOL")
    else:
        await update.message.reply_text("⚠️ Failed to fetch gas price.")

# Help Command
async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "🆘 Help:\n"
        "/start - Launch bot\n"
        "/portfolio [address] - Wallet holdings\n"
        "/gas - Network fees\n"
        "/whalealert - Setup alerts\n"
    )

# Whale Alert Setup (Stub for now)
async def whalealert(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("🛠️ Whale alerts under construction! Use /help.")

def main() -> None:
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("gas", gas))
    app.add_handler(CommandHandler("whalealert", whalealert))
    app.add_handler(CommandHandler("help", help_command))
    
    # Start Polling
    app.run_polling()

if __name__ == "__main__":
    main()