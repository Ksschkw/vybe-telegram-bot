from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from .db import get_user_favorites

async def favorite_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Lists a user's favorite tokens.
    Works as both a Slash Command (/favoritetokens) and a CallbackQuery (menu button).
    """
    # Figure out where to send:
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        send = query.message.reply_text
    else:
        send = update.message.reply_text

    user_id = update.effective_user.id
    favs = get_user_favorites(user_id)["tokens"]
    if not favs:
        await send(
            "⭐ You have no favorite tokens yet.\n"
            "Use /addfavoritetoken <mint> to add one."
        )
        return

    buttons = [
        [InlineKeyboardButton(f"{mint[:6]}…{mint[-4:]}", callback_data=f"fav_token:{mint}")]
        for mint in favs
    ]
    await send(
        "🌟 Your Favorite Tokens:\n\n"
        "Click one to manage it:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
