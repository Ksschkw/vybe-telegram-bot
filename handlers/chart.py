import time
import aiohttp
from datetime import datetime, UTC
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO

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

async def fetch_ohlcv(mint: str, resolution: str, start: int, end: int):
    """Hit Vybe’s OHLCV endpoint and return the raw data list."""
    url = f"https://api.vybenetwork.xyz/price/{mint}/token-ohlcv"
    headers = {
        "accept": "application/json",
        "X-API-KEY": __import__("os").getenv("VYBE_API_KEY"),
    }
    params = {"resolution": resolution, "timeStart": start, "timeEnd": end}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as resp:
            resp.raise_for_status()
            body = await resp.json()
    return body.get("data", [])

def generate_price_chart(dates, closes):
    """Plot dates vs. closes and return a PNG BytesIO."""
    plt.figure(figsize=(8, 4))
    plt.plot(dates, closes)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.xticks(rotation=45)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close()
    buf.seek(0)
    return buf

async def start_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the Chart menu."""
    await update.callback_query.answer()
    USER_STATE[update.effective_user.id] = {"flow": "chart", "step": None}
    kb = [
        [
            InlineKeyboardButton("7 Days",  callback_data="chart_7d"),
            InlineKeyboardButton("30 Days", callback_data="chart_30d"),
        ],
        [InlineKeyboardButton("Custom Range", callback_data="chart_custom")],
    ]
    await update.callback_query.message.reply_text(
        "📈 *Chart Menu*\n\n"
        "Choose 7 day, 30 day, or Custom Range:",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )

async def chart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Record user’s choice (7d, 30d, or custom) and prompt for a mint or dates."""
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    choice = q.data.split("_")[1]

    state = USER_STATE[uid]
    state["step"] = choice

    if choice in ("7d", "30d"):
        await q.message.reply_text("🔎 Send token mint (the 44-char address):")
    else:  # custom
        await q.message.reply_text(
            "🗓️ Send two Unix timestamps for start and end (e.g. `1680000000 1682601600`):"
        )

async def handle_chart_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Consume the user’s follow-up message, fetch data, and send the chart."""
    uid = update.effective_user.id
    state = USER_STATE.get(uid)
    if not state or state.get("flow") != "chart":
        return

    text = update.message.text.strip()
    step = state["step"]

    # Determine timeframe
    now = int(time.time())
    if step == "7d":
        days = 7
        start, end = now - days * 86400, now
        mint = text
    elif step == "30d":
        days = 30
        start, end = now - days * 86400, now
        mint = text
    else:  # custom
        try:
            parts = text.split()
            if len(parts) != 2:
                raise ValueError("need exactly two timestamps")
            start, end = map(int, parts)
        except Exception as e:
            await update.message.reply_text(
                f"❌ Invalid input. Send two Unix timestamps, e.g. `1680000000 1682601600`."
            )
            return
        # now prompt for mint
        await update.message.reply_text("🔎 Now send token mint:")
        state["step"] = "custom_mint"
        state["range"] = (start, end)
        return

    # If custom_mint stage
    if step == "custom_mint":
        mint = text
        start, end = state["range"]

    # Fetch & plot
    try:
        data = await fetch_ohlcv(mint, "1d", start, end)
        if not data:
            raise ValueError("no data returned from API")
        dates = [datetime.fromtimestamp(pt["time"], tz=UTC) for pt in data]
        closes = [float(pt["close"]) for pt in data]
        buf = generate_price_chart(dates, closes)
        await update.message.reply_photo(buf)
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to fetch or plot data: {e}")

    USER_STATE.pop(uid)

handlers = [
    CallbackQueryHandler(chart_callback, pattern="^chart_"),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chart_input),
]
