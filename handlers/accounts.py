import requests, aiohttp
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes

# In-memory per-user flow state
USER_STATE = {}

def chunk_message(text: str, size: int = 4096):
    return [text[i : i + size] for i in range(0, len(text), size)]

async def fetch_known_accounts() -> list:
    """Fetch the real known accounts from Vybe."""
    url = "https://api.vybenetwork.xyz/account/known-accounts"
    headers = {
        "accept": "application/json",
        "X-API-KEY": __import__("os").getenv("VYBE_API_KEY")
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
    return data.get("accounts", [])

async def fetch_balance_ts(owner: str) -> list:
    """Fetch the balance time-series for a given wallet."""
    url = f"https://api.vybenetwork.xyz/account/token-balance-ts/{owner}"
    headers = {
        "accept": "application/json",
        "X-API-KEY": __import__("os").getenv("VYBE_API_KEY")
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
    # expected format: [{'timestamp': ..., 'balanceUsd': ...}, ...]
    return data.get("data", [])

async def get_wallet_balance(wallet_address: str) -> str:
    """Fetch and format wallet balance."""
    url = f"https://api.vybenetwork.xyz/account/token-balance/{wallet_address}"
    headers = {
        "accept": "application/json",
        "X-API-KEY": __import__("os").getenv("VYBE_API_KEY")
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    ts = data.get('date')
    formatted = datetime.fromtimestamp(ts/1000).strftime('%Y-%m-%d %H:%M:%S') if ts else "Unknown"
    sol    = float(data.get('stakedSolBalance', 0))
    total  = int(data.get('totalTokenCount', 0))
    val    = float(data.get('totalTokenValueUsd', 0))
    staked = float(data.get('activeStakedSolBalance', 0))

    return (
        f"💼 Wallet Overview 💼\n\n"
        f"🔑 `{wallet_address}`\n"
        f"🕒 Last Updated: {formatted}\n\n"
        f"💰 SOL: {sol:.4f}\n"
        f"📊 Tokens: {total:,}\n"
        f"💵 Value: ${val:.2f}\n"
        f"🔒 Staked SOL: {staked:.4f}"
    )

async def start_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the Accounts menu buttons."""
    await update.callback_query.answer()
    USER_STATE[update.effective_user.id] = {"flow": "accounts", "step": None}
    kb = [
        [InlineKeyboardButton("Known",       callback_data="acct_known")],
        [InlineKeyboardButton("Balance",     callback_data="acct_balance")],
        [InlineKeyboardButton("Balance TS",  callback_data="acct_balance_ts")],
    ]
    await update.callback_query.message.reply_text(
        "💼 *Accounts Menu*\nChoose an option:",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

async def accounts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Record submenu choice and prompt."""
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    action = q.data.split("_")[1]
    USER_STATE[uid]["step"] = action

    if action == "known":
        await q.message.reply_text("Fetching known accounts…")
    elif action == "balance":
        await q.message.reply_text("🔍 Send wallet address for balance:")
    else:  # balance_ts
        await q.message.reply_text("📈 Send wallet address for time series:")

async def handle_accounts_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the user's reply for the Accounts menu."""
    uid = update.effective_user.id
    state = USER_STATE.get(uid)
    if not state or state.get("flow") != "accounts":
        return

    step = state["step"]
    text = update.message.text.strip()

    if step == "known":
        # Known accounts flow
        try:
            accounts = await fetch_known_accounts()
            if not accounts:
                await update.message.reply_text("🗒 No known accounts found.")
            else:
                lines = ["🗒 *Known Accounts:*"]
                for i, acct in enumerate(accounts, start=1):
                    name   = acct.get("name") or "N/A"
                    addr   = acct.get("ownerAddress", "N/A")
                    labels = ", ".join(acct.get("labels", [])) or "None"
                    lines.append(f"{i}. *{name}* — `{addr}` ({labels})")
                await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to fetch known accounts: {e}")

    elif step == "balance":
        # Single-balance flow
        try:
            res = await get_wallet_balance(text)
            for chunk in chunk_message(res):
                await update.message.reply_text(chunk, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error fetching wallet balance: {e}")

    else:  # balance_ts
        # Time-series flow
        try:
            series = await fetch_balance_ts(text)
            if not series:
                await update.message.reply_text("📈 No time-series data found.")
            else:
                lines = ["📈 *Balance Time Series:*"]
                for i, point in enumerate(series, start=1):
                    ts = point.get("timestamp")
                    dt = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') if ts else "N/A"
                    bal = point.get("balanceUsd", 0)
                    lines.append(f"{i}. {dt} → ${bal:.2f}")
                # chunk if too long
                for chunk in chunk_message("\n".join(lines)):
                    await update.message.reply_text(chunk, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error fetching time-series: {e}")

    USER_STATE.pop(uid)

handlers = [
    CallbackQueryHandler(accounts_callback, pattern="^acct_"),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_accounts_input),
]
