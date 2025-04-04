import logging
import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler,
    InlineQueryHandler
)
from vybe_api import VybeAPI
from config import Config
from constants import HELP_TEXT
#for railway?
# Add new imports
# import threading
# from flask import Flask

# # Create healthcheck server
# app = Flask(__name__)

# @app.route('/')
# def healthcheck():
#     return "Vybe Bot Operational", 200

# def run_flask():
#     app.run(host='0.0.0.0', port=3000)
from dotenv import load_dotenv

load_dotenv()
VYBE_API_KEY = os.getenv("VYBE_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

vybe = VybeAPI()

# Conversation states
SET_ALERT, GET_WALLET = range(2)

async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("💰 Portfolio", callback_data="portfolio"),
         InlineKeyboardButton("🐳 Whale Alerts", callback_data="whale")],
        [InlineKeyboardButton("⛽ Gas Prices", callback_data="gas"),
         InlineKeyboardButton("🖼 NFT Holdings", callback_data="nft")],
    ]
    await update.message.reply_text(
        "🔮 *Vybe Analytics Bot*\nChoose an option:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_help(update: Update, context: CallbackContext):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")

async def handle_gas(update: Update, context: CallbackContext):
    gas_data = vybe.get_gas_prices()
    response = (
        "⛽ *Current Gas Prices*\n\n"
        f"Low: {gas_data['low']} gwei\n"
        f"Average: {gas_data['average']} gwei\n"
        f"High: {gas_data['high']} gwei"
    )
    await update.message.reply_text(response, parse_mode="Markdown")

async def handle_portfolio(update: Update, context: CallbackContext):
    try:
        address = context.args[0]
        portfolio = vybe.get_portfolio(address)
        response = (
            f"📊 *Portfolio for {address[:6]}...*\n\n"
            f"Total Value: ${portfolio['total_value']}\n"
            f"24h Change: {portfolio['24h_change']}%\n"
            f"Top Asset: {portfolio['top_asset']['symbol']} (${portfolio['top_asset']['value']})"
        )
        await update.message.reply_text(response, parse_mode="Markdown")
    except IndexError:
        await update.message.reply_text("Please provide a wallet address\nExample: /portfolio 0x...")

async def handle_whale_alert(update: Update, context: CallbackContext):
    try:
        threshold = int(context.args[0])
        Config.ALERT_THRESHOLD = threshold
        await update.message.reply_text(f"🔔 Whale alert threshold set to ${threshold}")
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid number\nExample: /whalealert 1000000")

async def handle_query(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data == "portfolio":
        await query.edit_message_text("Enter wallet address:")
        return GET_WALLET
    elif query.data == "whale":
        await query.edit_message_text("Enter minimum alert value (USD):")
        return SET_ALERT
    elif query.data == "gas":
        await handle_gas(update, context)
    elif query.data == "nft":
        await query.edit_message_text("Enter wallet address for NFT lookup:")
        return GET_WALLET

async def handle_message(update: Update, context: CallbackContext):
    user_data = context.user_data
    text = update.message.text
    
    if 'awaiting' in user_data:
        if user_data['awaiting'] == 'wallet':
            balance = vybe.get_wallet_balance(text)
            response = (
                f"💼 *Wallet Balance*\n\n"
                f"ETH: {balance['eth']}\n"
                f"USD Value: ${balance['usd_value']}\n"
                f"Assets: {len(balance['tokens'])} tokens"
            )
            await update.message.reply_text(response, parse_mode="Markdown")
        user_data.clear()

async def error_handler(update: Update, context: CallbackContext):
    logger.error(msg="Exception while handling update:", exc_info=context.error)
    await update.message.reply_text("⚠️ Error processing request. Please try again.")

async def inline_query(update: Update, context: CallbackContext):
    query = update.inline_query.query
    results = []
    
    try:
        if query.startswith('0x'):
            # Wallet address lookup
            balance = vybe.get_wallet_balance(query)
            results.append(InlineQueryResultArticle(
                id='1',
                title=f"Balance: {balance.get('eth', 'N/A')} ETH",
                input_message_content=InputTextMessageContent(
                    f"💰 Wallet Balance\n\nETH: {balance.get('eth', 'N/A')}\n"
                    f"USD Value: ${balance.get('usd_value', 'N/A')}"
                )
            ))
        elif query.lower() == 'gas':
            gas_data = vybe.get_gas_prices()
            results.append(InlineQueryResultArticle(
                id='2',
                title="Current Gas Prices",
                input_message_content=InputTextMessageContent(
                    f"⛽ Gas Prices\n\n"
                    f"Low: {gas_data.get('low', 'N/A')} gwei\n"
                    f"Average: {gas_data.get('average', 'N/A')} gwei\n"
                    f"High: {gas_data.get('high', 'N/A')} gwei"
                )
            ))
            
    except Exception as e:
        logger.error(f"Inline query error: {e}")
    
    await update.inline_query.answer(results)
async def handle_wallet_input(update: Update, context: CallbackContext):
    address = update.message.text
    try:
        portfolio = vybe.get_portfolio(address)
        response = (
            f"📊 *Portfolio for {address[:6]}...*\n\n"
            f"Total Value: ${portfolio.get('total_value', 'N/A')}\n"
            f"24h Change: {portfolio.get('24h_change', 'N/A')}%\n"
            f"Top Asset: {portfolio.get('top_asset', {}).get('symbol', 'N/A')} "
            f"(${portfolio.get('top_asset', {}).get('value', 'N/A')})"
        )
        await update.message.reply_text(response, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error handling wallet input: {e}")
        await update.message.reply_text("❌ Error fetching wallet data")
    return ConversationHandler.END

async def handle_alert_input(update: Update, context: CallbackContext):
    try:
        threshold = int(update.message.text)
        Config.ALERT_THRESHOLD = threshold
        await update.message.reply_text(f"🔔 Whale alert threshold set to ${threshold}")
    except ValueError:
        await update.message.reply_text("⚠️ Please enter a valid number")
    return ConversationHandler.END

def main():
    # PORT = int(os.environ.get('PORT', 8443)) #for railway?
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Handlers
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_query)],
        states={
            GET_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wallet_input)],
            SET_ALERT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_alert_input)]
        },
        fallbacks=[CommandHandler("cancel", start)],
    )
    # if 'RAILWAY_ENVIRONMENT' in os.environ:
    #     application.run_webhook(
    #         listen="0.0.0.0",
    #         port=PORT,
    #         url_path=TELEGRAM_TOKEN,
    #         webhook_url=f"https://{os.environ['RAILWAY_STATIC_URL']}/{TELEGRAM_TOKEN}"
    #     )
    # else:
    #     application.run_polling()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", handle_help))
    application.add_handler(CommandHandler("gas", handle_gas))
    application.add_handler(CommandHandler("portfolio", handle_portfolio))
    application.add_handler(CommandHandler("whalealert", handle_whale_alert))
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    application.add_handler(InlineQueryHandler(inline_query))

    
    # Start polling
    application.run_polling()
    # if 'RAILWAY_ENVIRONMENT' in os.environ:
    #     flask_thread = threading.Thread(target=run_flask)
    #     flask_thread.start()

if __name__ == "__main__":
    main()