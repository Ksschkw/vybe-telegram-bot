import aiohttp
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Per-user state for interactive flows
USER_STATE = {}

async def detect_whale_transfers(cap: float = 1000.0) -> list:
    """Fetch transfers ≥ cap USD and return filtered list."""
    url = "https://api.vybenetwork.xyz/token/transfers"
    headers = {"accept": "application/json", "X-API-KEY": __import__("os").getenv("VYBE_API_KEY")}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
    out = []
    for t in data.get("transfers", []):
        try:
            v = float(t.get("valueUsd", "0"))
        except:
            continue
        if v >= cap:
            out.append({
                "signature": t.get("signature"),
                "sender":    t.get("senderAddress"),
                "receiver":  t.get("receiverAddress"),
                "amount":    t.get("calculatedAmount"),
                "value":     v,
                "time":      t.get("blockTime")
            })
    return out

def chunk_message(text: str, size: int = 4096) -> list:
    """Split a long text into Telegram-safe chunks."""
    return [text[i : i + size] for i in range(0, len(text), size)]

async def start_whale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the whale alerts menu."""
    await update.callback_query.answer()
    USER_STATE[update.effective_user.id] = {"flow": "whale", "step": None}
    kb = [
        [InlineKeyboardButton("Default ≥ $1,000", callback_data="whale_default")],
        [InlineKeyboardButton("Custom Threshold", callback_data="whale_custom")]
    ]
    await update.callback_query.message.reply_text(
        "🐋 *Whale Alerts*\n\n"
        "• Default: transfers ≥ $1,000 USD\n"
        "• Custom: pick your own threshold and count\n\n"
        "Or send `/whalealert [threshold] [count]` directly.",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

async def whale_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle menu button presses."""
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "whale_default":
        # Immediately fetch with default cap=1000, count=7
        alerts = await detect_whale_transfers(1000.0)
        await _send_alerts(q.message.chat_id, alerts, threshold=1000.0, count=7, context=context)
        USER_STATE.pop(uid, None)

    elif q.data == "whale_custom":
        # Ask for threshold first
        USER_STATE[uid]["step"] = "threshold"
        await q.message.reply_text("📊 Send me the USD threshold (e.g. `5000`):")

async def handle_whale_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process text inputs for custom threshold/count."""
    uid = update.effective_user.id
    state = USER_STATE.get(uid)
    if not state or state.get("flow") != "whale":
        return

    text = update.message.text.strip()

    if state["step"] == "threshold":
        # Parse threshold, then ask count
        try:
            thr = float(text)
            state["threshold"] = thr
            state["step"] = "count"
            await update.message.reply_text(f"✅ Threshold set to ${thr:.0f}. Now send max number of alerts (e.g. `5`):")
        except:
            await update.message.reply_text("❌ Invalid threshold. Send a number like `1000`.")
    elif state["step"] == "count":
        # Parse count and display
        try:
            cnt = int(text)
            thr = state.get("threshold", 1000.0)
            alerts = await detect_whale_transfers(thr)
            await _send_alerts(update.message.chat_id, alerts, threshold=thr, count=cnt, context=context)
        except:
            await update.message.reply_text("❌ Invalid count. Send a whole number like `7`.")
        finally:
            USER_STATE.pop(uid, None)
    else:
        # Shouldn’t happen
        USER_STATE.pop(uid, None)

async def _send_alerts(chat_id: int, alerts: list, threshold: float, count: int, context):
    """Helper to format and send numbered alerts."""
    alerts = alerts[:count]
    if not alerts:
        await context.bot.send_message(chat_id, f"No whale transfers ≥ ${threshold:.0f} found.")
        return

    lines = [f"🐋 **Top {len(alerts)} Whale Transfers** (≥ ${threshold:.0f}):\n"]
    for i, t in enumerate(alerts, start=1):
        ts = t["time"]
        ts_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') if ts else "N/A"
        lines.append(
            f"**{i}.** \n • Signature : `{t['signature']}`\n"
            f"  • From: `{t['sender']}`\n"
            f"  • To:   `{t['receiver']}`\n"
            f"  • Amount: {t['amount']}\n"
            f"  • Value:  ${t['value']:.2f}\n"
            f"  • Time:   {ts_str} UTC\n"
        )

    text = "\n".join(lines)
    for chunk in chunk_message(text):
        await context.bot.send_message(chat_id, chunk, parse_mode="Markdown")

handlers = [
    CallbackQueryHandler(whale_callback, pattern="^whale_"),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_whale_input)
]
