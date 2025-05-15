# favorites_handlers/callbacks.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from slashcommands.slashutils import (
    get_wallet_balance,
    chunk_message,
    get_token_details,
    get_top_token_holders
)
from .favorite_accounts import favorite_accounts
from .favorite_tokens import favorite_tokens

async def favorites_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kind, addr = query.data.split(":", 1)

    if kind == "fav_acct":
        kb = [
            [InlineKeyboardButton("🔄 Balance", callback_data=f"acc_balance:{addr}")],
            [InlineKeyboardButton("← Back", callback_data="back_fav_acct")]
        ]
        await query.edit_message_text(
            f"📋 Account Menu for `{addr[:6]}…{addr[-4:]}`",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode=None
        )

    elif kind == "fav_token":
        kb = [
            [InlineKeyboardButton("🔍 Details", callback_data=f"tok_details:{addr}")],
            [InlineKeyboardButton("👑 Top Holders", callback_data=f"tok_holders:{addr}")],
            [InlineKeyboardButton("← Back", callback_data="back_fav_tok")]
        ]
        await query.edit_message_text(
            f"📋 Token Menu for `{addr[:6]}…{addr[-4:]}`",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode=None
        )

async def account_balance_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, wallet_address = query.data.split(":", 1)

    result_text = await get_wallet_balance(wallet_address)
    for chunk in chunk_message(result_text):
        await query.message.reply_text(chunk, parse_mode=None)

async def token_details_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, mint_address = query.data.split(":", 1)

    result_text = await get_token_details(mint_address)
    for chunk in chunk_message(result_text):
        await query.message.reply_text(chunk, parse_mode=None)

async def token_holders_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch and display the full addresses of top token holders."""
    query = update.callback_query
    await query.answer()
    _, mint_address = query.data.split(":", 1)

    holders = await get_top_token_holders(mint_address)
    if not holders:
        await query.message.reply_text("No holders data available.", parse_mode=None)
        return

    # Build each line with the full address
    lines = []
    for i, h in enumerate(holders, start=1):
        addr = h.get("ownerAddress") or h.get("address") or "Unknown"
        amount = h.get("amount", "N/A")
        lines.append(f"{i}. `{addr}` – {amount}")

    text = (
        f"👑 Top Holders for `{mint_address}`\n\n"
        + "\n".join(lines)
    )

    # Send in chunks if too long
    for chunk in chunk_message(text):
        await query.message.reply_text(chunk, parse_mode=None)

async def back_to_fav_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await favorite_accounts(update, context)

async def back_to_fav_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await favorite_tokens(update, context)
