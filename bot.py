from telegram import InlineKeyboardMarkup, Update, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config import TELEGRAM_TOKEN
from slashcommands.slashmain import (
    handle_typos,
    get_balance,
    whale_alert,
    check_prices,
    token_details,
    top_token_holders,
    chart,
    nft_analysis,
    tutorial_start,
    tutorial_callback
)
from handlers.state import USER_STATE  # Import global USER_STATE
import handlers.start as start_h
import handlers.accounts as acct_h
import handlers.prices as prices_h
import handlers.chart as chart_h
import handlers.holders as holders_h
import handlers.nft_analysis as nft_h
import handlers.pyth as pyth_h
import handlers.tutorial as tut_h
import handlers.whale_alert as whale_h
import logging

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

app = Application.builder().token(TELEGRAM_TOKEN).build()
from favorites_handlers.add_favorite_account import add_favorite_account
from favorites_handlers.favorite_accounts import favorite_accounts
from favorites_handlers.add_favorite_token import add_favorite_token
from favorites_handlers.favorite_tokens import favorite_tokens
from favorites_handlers.callbacks import (
    favorites_callback,
    account_balance_cb,
    token_details_cb,
    token_holders_cb,
    back_to_fav_accounts,
    back_to_fav_tokens
)

app.add_handler(CommandHandler("addfavoriteaccount", add_favorite_account))
app.add_handler(CommandHandler("favoriteaccounts", favorite_accounts))
app.add_handler(CommandHandler("addfavoritetoken", add_favorite_token))
app.add_handler(CommandHandler("favoritetokens", favorite_tokens))
app.add_handler(CallbackQueryHandler(favorites_callback, pattern="^fav_(acct|token):"))
app.add_handler(CallbackQueryHandler(account_balance_cb, pattern="^acc_balance:"))
app.add_handler(CallbackQueryHandler(token_details_cb, pattern="^tok_details:"))
app.add_handler(CallbackQueryHandler(token_holders_cb, pattern="^tok_holders:"))
app.add_handler(CallbackQueryHandler(back_to_fav_accounts, pattern="^back_fav_acct$"))
app.add_handler(CallbackQueryHandler(back_to_fav_tokens, pattern="^back_fav_tok$"))

# Modified handle_typos to skip chart flow
async def handle_typos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = USER_STATE.get(uid, {})
    if state.get("flow") == "chart":
        # logger.info(f"handle_typos: Skipped for user {uid} in chart flow, state: {state}")
        return
    # logger.info(f"handle_typos: User {uid}, input: '{update.message.text}'")
    keyboard =  [InlineKeyboardButton("ALPHAVYBE", url="https://vybe.fyi/")]
    await update.message.reply_text(
        "🤖Try these:\n"
        "• /start - Show main menu\n"
        "• /tutorial - Beginner's guide\n"
        "• Type /commands for full list",
        reply_markup=InlineKeyboardMarkup([keyboard]),
        )

# Handler Registration
app.add_handlers([
    CommandHandler("start", start_h.start),
    CommandHandler("help", start_h.start),
    CommandHandler("commands", start_h.show_commands),
    CommandHandler("balance", get_balance),
    CommandHandler("whalealert", whale_alert),
    CommandHandler("prices", check_prices),
    CommandHandler("tokenDetails", token_details),
    CommandHandler("topholders", top_token_holders),
    CommandHandler("chart", chart),
    CommandHandler("nft_analysis", nft_analysis),
    CommandHandler("tutorial", tutorial_start)
])

app.add_handlers([
    *start_h.menu_handlers,
    CallbackQueryHandler(tutorial_callback, pattern="^tutorial_"),
    CallbackQueryHandler(whale_h.start_whale, pattern="^menu_whale$")
])

all_flow_handlers = [
    *chart_h.handlers,
    *pyth_h.handlers,
    *acct_h.handlers,
    *prices_h.handlers,
    *holders_h.handlers,
    *nft_h.handlers,
    *tut_h.handlers,
    *whale_h.handlers
]

for handler in all_flow_handlers:
    app.add_handler(handler, group=0)

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.Regex(r'^/'),
        handle_typos
    ),
    group=50
)

if __name__ == "__main__":
    app.run_polling()