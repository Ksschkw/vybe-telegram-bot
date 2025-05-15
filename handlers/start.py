from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest
from handlers.state import USER_STATE

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the main menu with full emoji-rich descriptions."""
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
            InlineKeyboardButton("⭐ Fav Accts", callback_data="menu_fav_acct"),
            InlineKeyboardButton("⭐ Fav Toks", callback_data="menu_fav_tok")
        ],
        [
            InlineKeyboardButton("🖼 NFT Analysis", callback_data="menu_nft"),
            InlineKeyboardButton("⚙️ Pyth Data", callback_data="menu_pyth")
        ],
        [
            InlineKeyboardButton("🐋 Whale Alerts", callback_data="menu_whale"),
            InlineKeyboardButton("🎓 Tutorial", callback_data="menu_tutorial")
        ],
        [InlineKeyboardButton("🔗 ALPHAVYBE", url="https://vybe.fyi/")]
    ]

    message_text = (
        "🚀 Vybe Analytics Bot — Your Solana Alpha Sidekick!\n\n"
        "👇 Choose a button below or use a slash command.\n\n"
        "📋 Available Slash Commands:\n\n"
        "🔍 /balance <wallet> — Check SOL/token balance of any wallet\n"
        "📈 /chart <mint> — Token price chart from Birdeye\n"
        "📊 /prices [mint] [count] — Top token prices or specific token\n"
        "🐋 /whalealert [threshold] [count] — Recent large transactions\n"
        "🔎 /tokendetails <mint> — Details like supply, holders, volume\n"
        "👑 /topholders <mint> [count] — Richest holders of any token\n"
        "🖼 /nft_analysis <collection> — Floor price, volume & more\n"
        "⚙️ /pyth <feed_id> — Get real-time Pyth oracle data\n"
        "⭐ /addfavoriteaccount <account> — Save wallet to your list\n"
        "⭐ /favoriteaccounts — View your saved accounts\n"
        "⭐ /addfavoritetoken <mint> — Save a token to your list\n"
        "⭐ /favoritetokens — View your saved tokens\n"
        "🎓 /tutorial — Learn how to use the bot step-by-step\n"
        "📃 /commands — View all available commands\n"
    )

    await update.message.reply_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=None,
        disable_web_page_preview=True
    )


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to the main menu with full layout."""
    query = update.callback_query
    await query.answer()

    try:
        await query.edit_message_text(
            text=await generate_menu_text(),
            reply_markup=await generate_menu_keyboard(),
            parse_mode=None,
            disable_web_page_preview=True
        )
    except BadRequest as e:
        if "Message is not modified" in str(e):
            await query.answer("✅ Already showing the main menu.")
        else:
            await query.message.reply_text(
                await generate_menu_text(),
                reply_markup=await generate_menu_keyboard(),
                parse_mode=None
            )
    USER_STATE.pop(query.from_user.id, None)


async def generate_menu_text():
    return (
        "🏠 Main Menu — Vybe Analytics Bot\n\n"
        "Use the buttons below or type any command:\n"
        "• /balance\n"
        "• /chart\n"
        "• /prices\n"
        "• /whalealert\n"
        "• /tokendetails\n"
        "• /topholders\n"
        "• /nft_analysis\n"
        "• /favoriteaccounts\n"
        "• /favoritetokens\n"
        "• /pyth\n"
        "• /tutorial\n"
    )


async def generate_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Prices", callback_data="menu_prices"),
         InlineKeyboardButton("📈 Chart", callback_data="menu_chart")],
        [InlineKeyboardButton("👛 Accounts", callback_data="menu_accounts"),
         InlineKeyboardButton("👑 Holders", callback_data="menu_holders")],
        [InlineKeyboardButton("⭐ Fav Accts", callback_data="menu_fav_acct"),
         InlineKeyboardButton("⭐ Fav Toks", callback_data="menu_fav_tok")],
        [InlineKeyboardButton("🖼 NFT", callback_data="menu_nft"),
         InlineKeyboardButton("⚙️ Pyth", callback_data="menu_pyth")],
        [InlineKeyboardButton("🐋 Whale", callback_data="menu_whale"),
         InlineKeyboardButton("🎓 Tutorial", callback_data="menu_tutorial")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="main_menu")],
        [InlineKeyboardButton("🔗 ALPHAVYBE", url="https://vybe.fyi/")]
    ])


async def show_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Full slash command reference with emoji and short descriptions."""
    commands_text = (
        "📜 *Vybe Slash Commands*\n\n"
        "🔍 /balance <wallet> — SOL + Token balances\n"
        "📈 /chart <mint> — Token chart from Birdeye\n"
        "📊 /prices [mint] [count] — Show token prices\n"
        "🐋 /whalealert [threshold] [count] — Whale transfers\n"
        "🔎 /tokendetails <mint> — Token info & stats\n"
        "👑 /topholders <mint> [count] — Richest token holders\n"
        "🖼 /nft_analysis <collection> — Floor, listings, volume\n"
        "⭐ /addfavoriteaccount <wallet> — Save a wallet\n"
        "⭐ /favoriteaccounts — Your saved wallets\n"
        "⭐ /addfavoritetoken <mint> — Save a token\n"
        "⭐ /favoritetokens — Your saved tokens\n"
        "⚙️ /pyth <feed_id> — Real-time oracle feed\n"
        "🎓 /tutorial — Learn to use the bot\n"
        "📃 /commands — This list\n"
    )
    await update.message.reply_text(
        commands_text,
        parse_mode=None,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
    )


# Menu navigation routing
from handlers.accounts import start_accounts
from handlers.prices import start_prices
from handlers.chart import start_chart
from handlers.holders import start_holders
from handlers.nft_analysis import start_nft
from handlers.pyth import start_pyth
from handlers.tutorial import tutorial_start
from slashcommands.slashmain import whale_alert
from favorites_handlers.favorite_accounts import favorite_accounts
from favorites_handlers.favorite_tokens import favorite_tokens

menu_handlers = [
    CallbackQueryHandler(start_accounts, pattern="^menu_accounts$"),
    CallbackQueryHandler(start_prices, pattern="^menu_prices$"),
    CallbackQueryHandler(start_chart, pattern="^menu_chart$"),
    CallbackQueryHandler(start_holders, pattern="^menu_holders$"),
    CallbackQueryHandler(start_nft, pattern="^menu_nft$"),
    CallbackQueryHandler(start_pyth, pattern="^menu_pyth$"),
    CallbackQueryHandler(tutorial_start, pattern="^menu_tutorial$"),
    CallbackQueryHandler(whale_alert, pattern="^menu_whale$"),
    CallbackQueryHandler(favorite_accounts, pattern="^menu_fav_acct$"),
    CallbackQueryHandler(favorite_tokens, pattern="^menu_fav_tok$"),
    CallbackQueryHandler(main_menu_callback, pattern="^main_menu$")
]