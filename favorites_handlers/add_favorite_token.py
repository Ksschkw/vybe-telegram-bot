from telegram import Update
from telegram.ext import ContextTypes
from .db import add_favorite

async def add_favorite_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /addfavoritetoken <token_mint_address>")
        return
    mint = context.args[0]
    new_list = add_favorite(user_id, "tokens", mint)
    await update.message.reply_text(f"✅ Added {mint} to your favorite tokens. Total: {len(new_list)}")