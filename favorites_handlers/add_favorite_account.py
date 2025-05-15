from telegram import Update
from telegram.ext import ContextTypes
from .db import add_favorite

async def add_favorite_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /addfavoriteaccount <wallet_address>")
        return
    address = context.args[0]
    new_list = add_favorite(user_id, "accounts", address)
    await update.message.reply_text(f"✅ Added {address} to your favorite accounts. Total: {len(new_list)}")