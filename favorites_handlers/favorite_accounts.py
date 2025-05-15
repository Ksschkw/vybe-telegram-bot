from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from .db import get_user_favorites

async def favorite_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Lists a user's favorite accounts.
    Works as both a Slash Command (/favoriteaccounts) and a CallbackQuery (menu button).
    """
    # Figure out where to send:
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        send = query.message.reply_text
    else:
        send = update.message.reply_text

    user_id = update.effective_user.id
    favs = get_user_favorites(user_id)["accounts"]
    if not favs:
        await send(
            "⭐ You have no favorite accounts yet.\n"
            "Use /addfavoriteaccount <address> to add one."
        )
        return

    buttons = [
        [InlineKeyboardButton(f"{addr[:6]}…{addr[-4:]}", callback_data=f"fav_acct:{addr}")]
        for addr in favs
    ]
    await send(
        "🌟 Your Favorite Accounts:\n\n"
        "Click one to manage it:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
