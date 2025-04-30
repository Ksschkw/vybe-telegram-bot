import aiohttp
from datetime import datetime
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


async def fetch_top_holders(mint: str, count: int):
    """Fetch the top holders for a given token mint."""
    url = f"https://api.vybenetwork.xyz/token/{mint}/top-holders"
    headers = {
        "accept": "application/json",
        "X-API-KEY": __import__("os").getenv("VYBE_API_KEY"),
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
    return data.get("data", [])[:count]


async def fetch_holders_ts(mint: str):
    """Fetch the holders time-series for a given token mint."""
    url = f"https://api.vybenetwork.xyz/token/{mint}/holders-ts"
    headers = {
        "accept": "application/json",
        "X-API-KEY": __import__("os").getenv("VYBE_API_KEY"),
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
    return data.get("data", [])


async def start_holders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the Holders menu."""
    await update.callback_query.answer()
    USER_STATE[update.effective_user.id] = {"flow": "holders", "step": None}
    kb = [
        [
            InlineKeyboardButton("Top Holders", callback_data="holders_top"),
            InlineKeyboardButton("Holders TS",  callback_data="holders_ts"),
        ]
    ]
    await update.callback_query.message.reply_text(
        "👑 *Holders Menu*\n\nChoose an option:",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )


async def holders_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Record which holders option was chosen and prompt for mint and optional count."""
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    choice = q.data.split("_")[1]  # "top" or "ts"
    USER_STATE[uid]["step"] = choice

    if choice == "top":
        await q.message.reply_text(
            "🔢 Send `<mint> <count>` to view top holders,\n"
            "e.g. `Grass7B4RdKfBCjTKg… 5`"
        )
    else:  # holders_ts
        await q.message.reply_text(
            "🗓️ Send token mint to view holders time-series,\n"
            "e.g. `Grass7B4RdKfBCjTKg…`"
        )


async def handle_holders_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the user’s reply for the Holders menu."""
    uid = update.effective_user.id
    state = USER_STATE.get(uid)
    if not state or state.get("flow") != "holders":
        return

    step = state["step"]
    text = update.message.text.strip()

    if step == "top":
        # Expect: "<mint> <count>"
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("❌ Usage: `<mint> <count>`")
        else:
            mint, cnt_str = parts
            try:
                count = int(cnt_str)
                holders = await fetch_top_holders(mint, count)
                if not holders:
                    await update.message.reply_text("👀 No holders data found.")
                else:
                    lines = [f"👑 *Top {len(holders)} Holders for* `{mint}`"]
                    for h in holders:
                        rank = h.get("rank")
                        addr = h.get("ownerAddress")
                        bal  = float(h.get("balance", 0))
                        usd  = float(h.get("valueUsd", 0))
                        pct  = float(h.get("percentageOfSupplyHeld", 0))
                        lines.append(
                            f"{rank}. `{addr}`\n"
                            f"    • Balance: {bal:.4f}\n"
                            f"    • Value: ${usd:,.2f}\n"
                            f"    • Supply %: {pct:.4f}%"
                        )
                    for chunk in chunk_message("\n\n".join(lines)):
                        await update.message.reply_text(chunk, parse_mode="Markdown")
            except Exception as e:
                await update.message.reply_text(f"❌ Error fetching top holders: {e}")

    else:  # holders_ts
        # Expect: "<mint>"
        mint = text
        try:
            series = await fetch_holders_ts(mint)
            if not series:
                await update.message.reply_text("📈 No holders time-series data found.")
            else:
                lines = [f"📈 *Holders Time-Series for* `{mint}`"]
                for point in series:
                    ts = point.get("holdersTimestamp")
                    dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S") if ts else "N/A"
                    n  = point.get("nHolders", 0)
                    lines.append(f"{dt} → {n} holders")
                for chunk in chunk_message("\n".join(lines)):
                    await update.message.reply_text(chunk, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error fetching holders time-series: {e}")

    USER_STATE.pop(uid)


handlers = [
    CallbackQueryHandler(holders_callback, pattern="^holders_"),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_holders_input),
]
