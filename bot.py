import logging
import os
from solders.pubkey import Pubkey
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler
)
from vybe_api import VybeAPI
from dotenv import load_dotenv

# Initialize environment
load_dotenv()

# Configuration
VYBE_API_KEY = os.getenv("VYBE_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ALERT_THRESHOLD = 1000000  # Default whale alert threshold
vybe = VybeAPI()

# Chat capacity simulation (65% used)
REMAINING_CAPACITY = 35  # This is a placeholder

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
GET_WALLET, SET_ALERT = range(2)

def is_valid_solana_address(address: str) -> bool:
    try:
        Pubkey.from_string(address)
        return True
    except ValueError:
        return False

async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("💰 Portfolio", callback_data="portfolio"),
         InlineKeyboardButton("🐳 Whale Alerts", callback_data="whale")],
        [InlineKeyboardButton("⛽ Gas Prices", callback_data="gas"),
         InlineKeyboardButton("🖼 NFT Holdings", callback_data="nft")]
    ]
    await update.message.reply_text(
        "🔮 Vybe Analytics Bot - Main Menu\nChoose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard))
    return f"Chat capacity remaining: {REMAINING_CAPACITY}%"

async def handle_help(update: Update, context: CallbackContext):
    help_text = (
        "🚀 Vybe Bot Commands:\n"
        "/start - Show main menu\n"
        "/wallet <address> - Check portfolio\n"
        "/token <mint> - Token details\n"
        "/gas - Current gas prices\n"
        "/whalealert <amount> - Set alert threshold\n"
        "/help - This message"
    )
    await update.message.reply_text(help_text)
    return f"Chat capacity remaining: {REMAINING_CAPACITY-2}%"

async def handle_gas(update: Update, context: CallbackContext):
    try:
        gas_data = vybe.get_gas_prices()
        response = (
            "⛽ Solana Gas Prices\n\n"
            f"Priority Fee: {gas_data.get('priority_fee', 'N/A')} µLamports\n"
            f"Base Fee: {gas_data.get('base_fee', 'N/A')} Lamports\n"
            f"Compute Units: {gas_data.get('compute_units', 'N/A')}"
        )
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Gas error: {str(e)}")
        await update.message.reply_text("⚠️ Error fetching gas prices")
    return f"Chat capacity remaining: {REMAINING_CAPACITY-3}%"

async def handle_portfolio(update: Update, context: CallbackContext):
    address = context.args[0] if context.args else None
    
    if not address or not is_valid_solana_address(address):
        await update.message.reply_text("❌ Invalid Solana address!")
        return f"Chat capacity remaining: {REMAINING_CAPACITY-1}%"

    try:
        token_data = vybe.get_token_balance(address)
        nft_data = vybe.get_nft_balance(address)
        
        response = (
            "📊 Portfolio Summary\n\n"
            f"Total Value: ${token_data.get('total_usd_value', 0):.2f}\n"
            f"Tokens: {len(token_data.get('items', []))}\n"
            f"NFTs: {len(nft_data.get('items', []))}\n\n"
            f"🔗 [View on Solscan](https://solscan.io/account/{address})"
        )
        await update.message.reply_text(response, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Portfolio error: {str(e)}")
        await update.message.reply_text("⚠️ Error fetching portfolio")
    return f"Chat capacity remaining: {REMAINING_CAPACITY-4}%"

async def handle_whale_alert(update: Update, context: CallbackContext):
    try:
        threshold = int(context.args[0])
        global ALERT_THRESHOLD
        ALERT_THRESHOLD = threshold
        await update.message.reply_text(f"🔔 Whale alert threshold set to ${threshold}")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /whalealert <dollar_amount>")
    return f"Chat capacity remaining: {REMAINING_CAPACITY-2}%"

async def handle_query(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data == "portfolio":
        await query.edit_message_text("Enter Solana wallet address:")
        return GET_WALLET
    elif query.data == "whale":
        await query.edit_message_text("Enter minimum alert amount (USD):")
        return SET_ALERT
    elif query.data == "gas":
        return await handle_gas(update, context)
    return f"Chat capacity remaining: {REMAINING_CAPACITY-1}%"

async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    
    if not is_valid_solana_address(text):
        await update.message.reply_text("❌ Invalid Solana address!")
        return ConversationHandler.END
    
    try:
        # Unified portfolio handler
        return await handle_portfolio(update, context)
    except Exception as e:
        logger.error(f"Message error: {str(e)}")
        await update.message.reply_text("⚠️ Processing error")
    return f"Chat capacity remaining: {REMAINING_CAPACITY-3}%"

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_portfolio)],
            SET_ALERT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_whale_alert)]
        },
        fallbacks=[CommandHandler("cancel", start)]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", handle_help))
    application.add_handler(CommandHandler("gas", handle_gas))
    application.add_handler(CommandHandler("portfolio", handle_portfolio))
    application.add_handler(CommandHandler("whalealert", handle_whale_alert))
    application.add_handler(CallbackQueryHandler(handle_query))

    if os.environ.get('RAILWAY_ENVIRONMENT'):
        application.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 8443)),
            webhook_url=f"https://{os.environ['RAILWAY_STATIC_URL']}/webhook"
        )
    else:
        application.run_polling()

if __name__ == "__main__":
    main()