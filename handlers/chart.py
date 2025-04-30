# handlers/chart.py
import time
import aiohttp
from datetime import datetime, UTC
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes
from handlers.state import USER_STATE, CANCEL_BUTTON

def chunk_message(text: str, size: int = 4096) -> list:
    return [text[i:i+size] for i in range(0, len(text), size)]

async def fetch_ohlcv(mint: str, resolution: str, start: int, end: int) -> list:
    """Fetch OHLCV data from Vybe API"""
    url = f"https://api.vybenetwork.xyz/price/{mint}/token-ohlcv"
    headers = {
        "accept": "application/json",
        "X-API-KEY": __import__("os").getenv("VYBE_API_KEY"),
    }
    params = {"resolution": resolution, "timeStart": start, "timeEnd": end}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("data", [])
    except Exception as e:
        print(f"Error fetching OHLCV data: {e}")
        return []

def generate_price_chart(dates, closes, mint: str) -> BytesIO:
    """Generate price chart image"""
    plt.figure(figsize=(10, 5))
    plt.plot(dates, closes, color='#4B8BBE')
    plt.title(f"Price Chart for {mint[:6]}...{mint[-4:]}")
    plt.xlabel("Date")
    plt.ylabel("Price (USD)")
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100)
    plt.close()
    buf.seek(0)
    return buf

async def start_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiate chart flow"""
    await update.callback_query.answer()
    USER_STATE[update.effective_user.id] = {"flow": "chart", "step": "timeframe"}
    
    keyboard = [
        [
            InlineKeyboardButton("7 Days", callback_data="chart_7d"),
            InlineKeyboardButton("30 Days", callback_data="chart_30d"),
        ],
        [
            InlineKeyboardButton("Custom Range", callback_data="chart_custom"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")
        ]
    ]
    
    await update.callback_query.message.reply_text(
        "📈 *Chart Settings*\nSelect timeframe:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def chart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle timeframe selection"""
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    choice = q.data.split("_")[1]
    
    USER_STATE[uid] = {
        "flow": "chart",
        "step": "input",
        "timeframe": choice,
        "message_id": q.message.message_id
    }
    
    if choice in ("7d", "30d"):
        prompt = "🔎 Send token mint address:"
    else:
        prompt = "📅 Send start and end timestamps (e.g. `1633046400 1635724800`):"
    
    await q.message.edit_text(
        prompt,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(CANCEL_BUTTON)
    )

async def handle_chart_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process user input based on current state"""
    uid = update.effective_user.id
    state = USER_STATE.get(uid, {})
    
    if state.get("flow") != "chart":
        return
    
    text = update.message.text.strip()
    
    try:
        if state["timeframe"] == "custom":
            # Handle custom timestamp input
            if not text.replace(" ", "").isdigit():
                raise ValueError("Invalid timestamp format")
                
            timestamps = list(map(int, text.split()))
            if len(timestamps) != 2:
                raise ValueError("Need exactly 2 timestamps")
                
            start, end = sorted(timestamps)
            if end - start < 3600:
                raise ValueError("Minimum 1 hour range required")
                
            USER_STATE[uid].update({
                "start": start,
                "end": end,
                "step": "mint_input"
            })
            
            await update.message.reply_text(
                "🔎 Now send the token mint address:",
                reply_markup=InlineKeyboardMarkup(CANCEL_BUTTON)
            )
            return
            
        elif state["timeframe"] in ("7d", "30d"):
            # Direct mint input
            days = 7 if state["timeframe"] == "7d" else 30
            now = int(time.time())
            start = now - (days * 86400)
            end = now
            
            dates, closes = await process_chart_data(text, start, end)
            await send_chart(update, text, dates, closes)
            
        elif state.get("step") == "mint_input":
            # Handle mint input after custom timestamps
            dates, closes = await process_chart_data(text, state["start"], state["end"])
            await send_chart(update, text, dates, closes)
            
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error: {str(e)}\nPlease try again:",
            reply_markup=InlineKeyboardMarkup(CANCEL_BUTTON)
        )
    finally:
        USER_STATE.pop(uid, None)

async def process_chart_data(mint: str, start: int, end: int) -> tuple:
    """Fetch and process chart data"""
    data = await fetch_ohlcv(mint, "1d", start, end)
    if not data:
        raise ValueError("No data available for this mint/time range")
        
    dates = [datetime.fromtimestamp(pt["time"], tz=UTC) for pt in data]
    closes = [float(pt["close"]) for pt in data]
    return dates, closes

async def send_chart(update: Update, mint: str, dates: list, closes: list):
    """Generate and send chart to user"""
    chart_image = generate_price_chart(dates, closes, mint)
    caption = f"📈 Price Chart for `{mint[:6]}...{mint[-4:]}`\n"
    
    await update.message.reply_photo(
        photo=chart_image,
        caption=caption,
        parse_mode="Markdown"
    )
    
    # Add follow-up actions
    await update.message.reply_text(
        "What would you like to do next?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 New Chart", callback_data="menu_chart")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
    )

async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle chart cancellation"""
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    USER_STATE.pop(uid, None)
    
    await query.message.edit_text(
        "❌ Chart operation cancelled",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📈 Try Again", callback_data="menu_chart")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
    )

handlers = [
    CallbackQueryHandler(start_chart, pattern="^menu_chart$"),
    CallbackQueryHandler(chart_callback, pattern="^chart_"),
    CallbackQueryHandler(cancel_operation, pattern="^cancel_operation$"),
    MessageHandler(
        filters.TEXT & ~filters.COMMAND & (
            filters.Regex(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$') |  # Mint address
            filters.Regex(r'^\d+\s+\d+$')  # Timestamps
        ),
        handle_chart_input
    )
]