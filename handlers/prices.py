import aiohttp
from datetime import datetime, UTC
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# per-user flow state
USER_STATE = {}

def chunk_message(text: str, size: int = 4096):
    return [text[i : i + size] for i in range(0, len(text), size)]


async def fetch_tokens(page: int = 1):
    url = "https://api.vybenetwork.xyz/tokens"
    headers = {
        "accept": "application/json",
        "X-API-KEY": __import__("os").getenv("VYBE_API_KEY"),
    }
    params = {"page": page}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()
    return data.get("data", [])


async def fetch_token_details(mint: str) -> dict:
    url = f"https://api.vybenetwork.xyz/token/{mint}"
    headers = {
        "accept": "application/json",
        "X-API-KEY": __import__("os").getenv("VYBE_API_KEY"),
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            resp.raise_for_status()
            return await resp.json()


async def start_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    USER_STATE[update.effective_user.id] = {"flow": "prices", "step": None}
    kb = [
        [
            InlineKeyboardButton("Top Tokens",    callback_data="prices_top"),
            InlineKeyboardButton("Single Token", callback_data="prices_single"),
        ]
    ]
    await update.callback_query.message.reply_text(
        "📊 *Prices Menu*\n\n"
        "• Top Tokens (list the top N tokens)\n"
        "• Single Token (lookup by mint address)",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )


async def prices_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    choice = q.data.split("_")[1]  # "top" or "single"
    USER_STATE[uid]["step"] = choice

    if choice == "top":
        await q.message.reply_text("🔢 Send number of tokens to list (e.g. `10`):")
    else:
        await q.message.reply_text("🔎 Send token mint address to lookup:")


async def handle_prices_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = USER_STATE.get(uid)
    if not state or state.get("flow") != "prices":
        return

    step = state["step"]
    text = update.message.text.strip()

    if step == "top":
        # Top N tokens
        try:
            n = int(text)
            tokens = await fetch_tokens(page=1)
            if not tokens:
                raise ValueError("no tokens returned")
            tokens = tokens[:n]
            lines = [f"📊 *Top {len(tokens)} Tokens*"]
            for t in tokens:
                sym   = t.get("symbol", "N/A")
                name  = t.get("name", "N/A")
                price = t.get("price", 0)
                p1d   = t.get("price1d", 0)
                p7d   = t.get("price7d", 0)
                mcap  = t.get("marketCap", 0)
                ut    = t.get("updateTime")
                dt    = datetime.fromtimestamp(ut, tz=UTC).strftime("%Y-%m-%d %H:%M") if ut else "N/A"

                lines.append(
                    f"*{sym} — {name}*\n"
                    f"• Price: ${price:.4f}  (1d: {p1d:+.2%}, 7d: {p7d:+.2%})\n"
                    f"• Market Cap: ${mcap:,.0f}\n"
                    f"• Updated: {dt}"
                )
            for chunk in chunk_message("\n\n".join(lines)):
                await update.message.reply_text(chunk, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error fetching top tokens: {e}")

    else:
        # Single token lookup
        mint = text
        try:
            td = await fetch_token_details(mint)
            # Format the token details
            sym   = td.get("symbol", "N/A")
            name  = td.get("name", "N/A")
            price = td.get("price", 0)
            p1d   = td.get("price1d", 0)
            p7d   = td.get("price7d", 0)
            supply = td.get("currentSupply", 0)
            mcap   = td.get("marketCap", 0)
            vol24  = td.get("usdValueVolume24h", 0)
            ut     = td.get("updateTime")
            dt     = datetime.fromtimestamp(ut, tz=UTC).strftime("%Y-%m-%d %H:%M") if ut else "N/A"

            msg = (
                f"*{sym} — {name}*\n\n"
                f"💵 Price: ${price:.4f}\n"
                f"📈 1d Change: {p1d:+.2%}    7d Change: {p7d:+.2%}\n"
                f"🔢 Supply: {supply:,.0f}\n"
                f"💰 Market Cap: ${mcap:,.0f}\n"
                f"📊 24h Volume: ${vol24:,.0f}\n"
                f"⏱ Updated: {dt}"
            )
            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error fetching token details: {e}")

    USER_STATE.pop(uid)


handlers = [
    CallbackQueryHandler(prices_callback, pattern="^prices_"),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prices_input),
]
