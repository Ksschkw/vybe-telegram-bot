import time
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


async def fetch_pyth_price(feed_id: str):
    url = f"https://api.vybenetwork.xyz/price/{feed_id}/pyth-price"
    headers = {"accept": "application/json", "X-API-KEY": __import__("os").getenv("VYBE_API_KEY")}
    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers=headers) as r:
            r.raise_for_status()
            return await r.json()


async def fetch_pyth_ohlc(feed_id: str, resolution: str, start: int, end: int, limit: int = None):
    url = f"https://api.vybenetwork.xyz/price/{feed_id}/pyth-price-ohlc"
    headers = {"accept": "application/json", "X-API-KEY": __import__("os").getenv("VYBE_API_KEY")}
    params = {"resolution": resolution, "timeStart": start, "timeEnd": end}
    if limit is not None:
        params["limit"] = limit
    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers=headers, params=params) as r:
            r.raise_for_status()
            data = await r.json()
    return data.get("data", [])


async def fetch_pyth_ts(feed_id: str, resolution: str, start: int, end: int, limit: int = None):
    url = f"https://api.vybenetwork.xyz/price/{feed_id}/pyth-price-ts"
    headers = {"accept": "application/json", "X-API-KEY": __import__("os").getenv("VYBE_API_KEY")}
    params = {"resolution": resolution, "timeStart": start, "timeEnd": end}
    if limit is not None:
        params["limit"] = limit
    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers=headers, params=params) as r:
            r.raise_for_status()
            data = await r.json()
    return data.get("data", [])


async def fetch_pyth_product(product_id: str):
    url = f"https://api.vybenetwork.xyz/price/{product_id}/pyth-product"
    headers = {"accept": "application/json", "X-API-KEY": __import__("os").getenv("VYBE_API_KEY")}
    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers=headers) as r:
            r.raise_for_status()
            return await r.json()


async def start_pyth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the Pyth menu."""
    await update.callback_query.answer()
    USER_STATE[update.effective_user.id] = {"flow": "pyth", "step": None}
    kb = [
        [
            InlineKeyboardButton("Price",       callback_data="pyth_price"),
            InlineKeyboardButton("OHLC",        callback_data="pyth_ohlc"),
        ],
        [
            InlineKeyboardButton("Time Series", callback_data="pyth_ts"),
            InlineKeyboardButton("Product",     callback_data="pyth_product"),
        ],
    ]
    await update.callback_query.message.reply_text(
        "⚙️ *Pyth Oracle Menu*\n\nChoose an option:",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )


async def pyth_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Record which Pyth endpoint to call and prompt for next inputs."""
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    choice = q.data.split("_")[1]  # price / ohlc / ts / product
    USER_STATE[uid]["step"] = choice

    if choice == "price":
        await q.message.reply_text("🔎 Send the Pyth priceFeedId:")
    elif choice == "product":
        await q.message.reply_text("🔎 Send the Pyth productId:")
    else:
        await q.message.reply_text(
            "🗓️ Send `<feedId> <resolution> <startUnix> <endUnix> [limit]`\n"
            "e.g. `FeedPubKey 1d 1680000000 1682601600 50`"
        )


async def handle_pyth_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Consume the user’s follow-up, call the appropriate endpoint, and reply."""
    uid = update.effective_user.id
    state = USER_STATE.get(uid)
    if not state or state.get("flow") != "pyth":
        return

    step = state["step"]
    parts = update.message.text.strip().split()

    try:
        if step == "price":
            feed_id = parts[0]
            data = await fetch_pyth_price(feed_id)
            await update.message.reply_text(f"📡 Pyth Price:\n```\n{data}\n```")
        elif step == "product":
            prod_id = parts[0]
            data = await fetch_pyth_product(prod_id)
            await update.message.reply_text(f"📦 Pyth Product:\n```\n{data}\n```")
        else:
            # OHLC or TS; expect at least 4 parts
            if len(parts) < 4:
                raise ValueError("need at least 4 arguments")
            feed_id, res, start_s, end_s = parts[:4]
            start, end = int(start_s), int(end_s)
            limit = int(parts[4]) if len(parts) >= 5 else None

            if step == "ohlc":
                series = await fetch_pyth_ohlc(feed_id, res, start, end, limit)
                header = "📊 Pyth OHLC"
            else:
                series = await fetch_pyth_ts(feed_id, res, start, end, limit)
                header = "📈 Pyth Time Series"

            if not series:
                await update.message.reply_text(f"{header}: no data returned.")
            else:
                lines = [f"{header} ({len(series)} points):"]
                for pt in series:
                    ts = pt.get("time", pt.get("timestamp", None))
                    dt = datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d %H:%M") if ts else "N/A"
                    # generic formatting: show all numeric fields
                    metrics = [f"{k}:{v}" for k, v in pt.items() if k not in ("time","timestamp")]
                    lines.append(f"{dt} → " + ", ".join(metrics))
                for chunk in chunk_message("\n".join(lines)):
                    await update.message.reply_text(chunk)
    except Exception as e:
        await update.message.reply_text(f"❌ Error in Pyth {step}: {e}")

    USER_STATE.pop(uid)


handlers = [
    CallbackQueryHandler(pyth_callback, pattern="^pyth_"),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pyth_input),
]