# handlers/start.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from handlers.state import USER_STATE  # Use shared state

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main menu with improved layout and command list"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Prices", callback_data="menu_prices"),
            InlineKeyboardButton("📈 Chart", callback_data="menu_chart")
        ],
        [
            InlineKeyboardButton("👛 Accounts", callback_data="menu_accounts"),
            InlineKeyboardButton("👑 Holders", callback_data="menu_holders")
        ],
        [
            InlineKeyboardButton("🖼 NFT Analysis", callback_data="menu_nft"),
            InlineKeyboardButton("⚙️ Pyth Data", callback_data="menu_pyth")
        ],
        [
            InlineKeyboardButton("🐋 Whale Alerts", callback_data="menu_whale"),
            InlineKeyboardButton("🎓 Tutorial", callback_data="menu_tutorial")
        ]
    ]

    message_text = (
        "🚀 *Vybe Analytics Bot*\n\n"
        "📋 *Available Commands:*\n"
        "▫️ /balance `<wallet>` - Check wallet balance\n"
        "▫️ /chart `<mint_address>` - Price chart\n"
        "▫️ /prices `[mint|count]` - Token prices\n"
        "▫️ /whalealert `[threshold]` - Large transactions\n"
        "▫️ /tokendetails `<mint>` - Token details\n"
        "▫️ /topholders `<mint>` - Top holders\n"
        "▫️ /nft_analysis `<collection>` - NFT stats\n"
        "▫️ /pyth `<feed_id>` - Oracle data\n\n"
        "🛠 *Interactive Menu:*"
    )

    await update.message.reply_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# Import handlers from their dedicated modules
from handlers.accounts import start_accounts
from handlers.prices import start_prices
from handlers.chart import start_chart
from handlers.holders import start_holders
from handlers.nft_analysis import start_nft
from handlers.pyth import start_pyth
from handlers.tutorial import tutorial_start
from slashmain        import whale_alert

menu_handlers = [
    CallbackQueryHandler(start_accounts, pattern="^menu_accounts$"),
    CallbackQueryHandler(start_prices, pattern="^menu_prices$"),
    CallbackQueryHandler(start_chart, pattern="^menu_chart$"),
    CallbackQueryHandler(start_holders, pattern="^menu_holders$"),
    CallbackQueryHandler(start_nft, pattern="^menu_nft$"),
    CallbackQueryHandler(start_pyth, pattern="^menu_pyth$"),
    CallbackQueryHandler(tutorial_start, pattern="^menu_tutorial$"),
    CallbackQueryHandler(whale_alert, pattern="^whale$"),
    # CallbackQueryHandler(start_whale_alert, pattern="^menu_whale$")  # Updated pattern
]