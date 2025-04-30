from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes

USER_STATE = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Accounts",    callback_data="menu_accounts"),
         InlineKeyboardButton("Prices",      callback_data="menu_prices")],
        [InlineKeyboardButton("Chart",       callback_data="menu_chart"),
         InlineKeyboardButton("Holders",     callback_data="menu_holders")],
        [InlineKeyboardButton("NFT Analytics",callback_data="menu_nft"),
         InlineKeyboardButton("Pyth",   callback_data="menu_pyth")],
        [InlineKeyboardButton("Tutorial",    callback_data="menu_tutorial")],
        [InlineKeyboardButton("Whale Alert",    callback_data="whale")]
    ]
    message_text = (
        "🚀 *Vybe Analytics Bot*\nChoose an option or send a slash command:\n\n"
        "📋 *Available commands:*\n"
        "🎮 /tutorial - Interactive beginner's guide\n"
        "🔍 /balance <wallet> - Check wallet balance\n"
        "📊 /chart <mint_address> - Get the price chart\n"
        "📊 /prices <token_mint(optional)> [token count(optional)] - Get token prices\n"
        "🐋 /whalealert <threshold(optional)> [alert count(optional)] - Latest large transactions\n"
        "🔎 /tokendetails <mintAddress> - Get token details\n"
        "👑 /topholders <mintAddress> [count(optional)] - View top holders of a token\n"
        "🖼 /nft_analysis <collection_address> - Get NFT collection statistics\n"
    )
    await update.message.reply_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# Map each menu to its handler in respective module
from handlers.accounts     import start_accounts
from handlers.prices       import start_prices
from handlers.chart        import start_chart
from handlers.holders      import start_holders
from handlers.nft_analysis import start_nft
from handlers.pyth         import start_pyth
from handlers.tutorial     import tutorial_start
from slashmain        import whale_alert

menu_handlers = [
    CallbackQueryHandler(start_accounts, pattern="^menu_accounts$"),
    CallbackQueryHandler(start_prices,   pattern="^menu_prices$"),
    CallbackQueryHandler(start_chart,    pattern="^menu_chart$"),
    CallbackQueryHandler(start_holders,  pattern="^menu_holders$"),
    CallbackQueryHandler(start_nft,      pattern="^menu_nft$"),
    CallbackQueryHandler(start_pyth,     pattern="^menu_pyth$"),
    CallbackQueryHandler(tutorial_start, pattern="^menu_tutorial$"),
    CallbackQueryHandler(whale_alert, pattern="^whale$")

]
