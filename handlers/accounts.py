import requests, json, aiohttp
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes

# In-memory user state
USER_STATE = {}

def chunk_message(text: str, size: int = 4096):
    return [text[i : i + size] for i in range(0, len(text), size)]

async def get_wallet_balance(wallet_address: str) -> str:
    """Fetch and format wallet balance."""
    url = f"https://api.vybenetwork.xyz/account/token-balance/{wallet_address}"
    headers = {"accept": "application/json", "X-API-KEY": __import__('os').getenv("VYBE_API_KEY")}
    try:
        resp = requests.get(url, headers=headers); resp.raise_for_status()
        data = resp.json()
        ts = data.get('date')
        formatted = datetime.fromtimestamp(ts/1000).strftime('%Y-%m-%d %H:%M:%S') if ts else "Unknown"
        sol = float(data.get('stakedSolBalance',0))
        total = int(data.get('totalTokenCount',0))
        val  = float(data.get('totalTokenValueUsd',0))
        staked = float(data.get('activeStakedSolBalance',0))
        return (
            f"💼 Wallet Overview 💼\n\n"
            f"🔑 `{wallet_address}`\n"
            f"🕒 Last Updated: {formatted}\n\n"
            f"💰 SOL: {sol:.4f}\n"
            f"📊 Tokens: {total:,}\n"
            f"💵 Value: ${val:.2f}\n"
            f"🔒 Staked SOL: {staked:.4f}"
        )
    except Exception as e:
        return f"❌ Error: {e}"

async def start_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    USER_STATE[update.effective_user.id] = {"flow":"accounts","step":None}
    kb = [
        [InlineKeyboardButton("Known", callback_data="acct_known")],
        [InlineKeyboardButton("Balance", callback_data="acct_balance")],
        [InlineKeyboardButton("Balance TS", callback_data="acct_balance_ts")],
    ]
    await update.callback_query.message.reply_text(
        "💼 *Accounts Menu*\nChoose an option:",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

async def accounts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    uid = q.from_user.id; action = q.data.split("_")[1]
    USER_STATE[uid]["step"] = action
    prompts = {
        "known":      "🗒 Known Accounts:\n1. AbC…1234\n2. XyZ…9876",
        "balance":    "🔍 Send wallet address for balance:",
        "balance_ts": "📈 Send wallet address for time series:"
    }
    await q.message.reply_text(prompts[action])

async def handle_accounts_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = USER_STATE.get(uid)
    if not state or state["flow"]!="accounts": return

    step = state["step"]
    text = update.message.text.strip()
    if step=="known":
        await update.message.reply_text("🗒 AbC…1234\nXyZ…9876")
    else:
        res = await get_wallet_balance(text)
        for chunk in chunk_message(res):
            await update.message.reply_text(chunk, parse_mode="Markdown")
    USER_STATE.pop(uid)

handlers = [
    CallbackQueryHandler(accounts_callback, pattern="^acct_"),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_accounts_input)
]
