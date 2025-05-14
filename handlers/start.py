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
        ],
        [InlineKeyboardButton("ALPHAVYBE", url="https://vybe.fyi/")]
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
        parse_mode="Markdown",  # Changed to more reliable MarkdownV2
        disable_web_page_preview=True
    )

from telegram.error import BadRequest

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Safe menu handler without Markdown"""
    query = update.callback_query
    await query.answer()
    
    try:
        await query.edit_message_text(
            text=await generate_menu_text(),
            reply_markup=await generate_menu_keyboard(),
            parse_mode=None,  # Disable Markdown
            disable_web_page_preview=True
        )
    except BadRequest as e:
        if "Message is not modified" in str(e):
            await query.answer("Already on main menu ✅")
        else:
            await query.message.reply_text(
                await generate_menu_text(),
                reply_markup=await generate_menu_keyboard(),
                parse_mode=None
            )
        # Clear any existing state
    USER_STATE.pop(query.from_user.id, None)

async def generate_menu_text():
    return (
        "🚀 Vybe Analytics Bot 🚀\n\n"
        "📋 Available Commands 📋\n"
        "• Balance: /balance\n"
        "• Chart: /chart\n"
        "• Prices: /prices\n"
        "• Whale Alerts: /whalealert\n"
        "• Token Details: /tokendetails\n"
        "• Top Holders: /topholders\n"
        "• NFT Analysis: /nft_analysis\n"
        "• Pyth Data: /pyth\n\n"
        "💡 Use the buttons below for quick access!"
    )

async def generate_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Prices 📊", callback_data="menu_prices"),
         InlineKeyboardButton("Chart 📈", callback_data="menu_chart")],
        [InlineKeyboardButton("Accounts 👛", callback_data="menu_accounts"),
         InlineKeyboardButton("Holders 👑", callback_data="menu_holders")],
        [InlineKeyboardButton("NFT Analysis 🖼", callback_data="menu_nft"),
         InlineKeyboardButton("Pyth Data ⚙️", callback_data="menu_pyth")],
        [InlineKeyboardButton("Whale Alerts 🐋", callback_data="menu_whale"),
         InlineKeyboardButton("Tutorial 🎓", callback_data="menu_tutorial")],
        [InlineKeyboardButton("Refresh Menu 🔄", callback_data="main_menu")],
        [InlineKeyboardButton("ALPHAVYBE", url="https://vybe.fyi/")]
    ])


async def show_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simplified commands list without Markdown"""
    commands_text = (
        "📜 Full Command List 📜\n\n"
        "• /start - Main menu\n"
        "• /balance <wallet> - Check wallet balance\n"
        "• /chart <mint> - Get price chart\n"
        "• /prices [mint|count] - Show token prices\n"
        "• /whalealert [threshold] - Large transactions\n"
        "• /tokendetails <mint> - Token details\n"
        "• /topholders <mint> - Top holders\n"
        "• /nft_analysis <collection> - NFT stats\n"
        "• /pyth <feed_id> - Oracle data\n"
        "• /tutorial - Learning guide\n"
        "• /commands - This help list"
    )
    
    await update.message.reply_text(
        commands_text,
        parse_mode=None,  # Disable Markdown
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Main Menu 🏠", callback_data="main_menu")]
        ])
    )

# Import handlers from their dedicated modules
from handlers.accounts import start_accounts
from handlers.prices import start_prices
from handlers.chart import start_chart
from handlers.holders import start_holders
from handlers.nft_analysis import start_nft
from handlers.pyth import start_pyth
from handlers.tutorial import tutorial_start
from slashcommands.slashmain        import whale_alert

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
    CallbackQueryHandler(main_menu_callback, pattern="^main_menu$")
]