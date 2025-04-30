# handlers/pyth.py
import aiohttp
from datetime import datetime, UTC
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes
from handlers.state import USER_STATE, CANCEL_BUTTON

def chunk_message(text: str, size: int = 4096) -> list:
    return [text[i:i+size] for i in range(0, len(text), size)]

async def fetch_pyth_data(endpoint: str, identifier: str, params: dict = None) -> dict:
    """Generic Pyth data fetcher"""
    url = f"https://api.vybenetwork.xyz/price/{identifier}/{endpoint}"
    headers = {
        "accept": "application/json",
        "X-API-KEY": __import__("os").getenv("VYBE_API_KEY"),
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                resp.raise_for_status()
                return await resp.json()
    except Exception as e:
        print(f"Pyth API Error ({endpoint}): {e}")
        return {}

async def start_pyth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiate Pyth oracle menu"""
    await update.callback_query.answer()
    USER_STATE[update.effective_user.id] = {"flow": "pyth", "step": "menu"}
    
    keyboard = [
        [InlineKeyboardButton("Price Feed", callback_data="pyth_price"),
         InlineKeyboardButton("OHLC Data", callback_data="pyth_ohlc")],
        [InlineKeyboardButton("Time Series", callback_data="pyth_ts"),
         InlineKeyboardButton("Product Info", callback_data="pyth_product")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]
    ]
    
    await update.callback_query.message.edit_text(
        "⚙️ *Pyth Oracle Menu*\nSelect data type:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def pyth_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Pyth data type selection"""
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data_type = q.data.split("_")[1]
    
    USER_STATE[uid] = {
        "flow": "pyth",
        "step": "input",
        "type": data_type,
        "message_id": q.message.message_id
    }
    
    prompts = {
        "price": "🔎 Enter Price Feed ID:",
        "product": "🔎 Enter Product ID:",
        "ohlc": "📝 Format: <FeedID> <Resolution> <Start> <End>\nExample: `FeedID 1h 1633046400 1635724800`",
        "ts": "📝 Format: <FeedID> <Resolution> <Start> <End>\nExample: `FeedID 4h 1633046400 1635724800`"
    }
    
    await q.message.edit_text(
        prompts[data_type],
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(CANCEL_BUTTON)
    )

async def handle_pyth_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process Pyth data input"""
    uid = update.effective_user.id
    state = USER_STATE.get(uid, {})
    
    if state.get("flow") != "pyth":
        return
    
    text = update.message.text.strip()
    data_type = state["type"]
    
    try:
        if data_type in ["price", "product"]:
            # Simple ID-based lookup
            result = await fetch_pyth_data(
                endpoint=f"pyth-{'price' if data_type == 'price' else 'product'}",
                identifier=text
            )
            response = format_simple_result(result, data_type)
            
        else:
            # OHLC/TS requires parameters parsing
            parts = text.split()
            if len(parts) < 4:
                raise ValueError("Need at least 4 parameters")
                
            feed_id, resolution, start, end = parts[:4]
            params = {
                "resolution": resolution,
                "timeStart": int(start),
                "timeEnd": int(end)
            }
            
            endpoint = "pyth-price-ohlc" if data_type == "ohlc" else "pyth-price-ts"
            data = await fetch_pyth_data(endpoint, feed_id, params)
            response = format_time_data(data, data_type)
            
        for chunk in chunk_message(response):
            await update.message.reply_text(chunk, parse_mode="Markdown")
            
    except ValueError as e:
        error_msg = f"❌ Invalid input: {str(e)}\nPlease try again:"
        await update.message.reply_text(error_msg, reply_markup=InlineKeyboardMarkup(CANCEL_BUTTON))
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}\nPlease try again:"
        await update.message.reply_text(error_msg, reply_markup=InlineKeyboardMarkup(CANCEL_BUTTON))
    finally:
        USER_STATE.pop(uid, None)
        await show_followup_menu(update)

def format_simple_result(data: dict, data_type: str) -> str:
    """Format simple price/product responses"""
    if not data:
        return "❌ No data found"
    
    if data_type == "price":
        return (
            f"📈 *Price Feed Data*\n\n"
            f"• Price: {data.get('price', 'N/A')}\n"
            f"• Confidence: {data.get('confidence', 'N/A')}\n"
            f"• Timestamp: {datetime.fromtimestamp(data.get('timestamp', 0), UTC)}"
        )
    return (
        f"📦 *Product Info*\n\n"
        f"• Base: {data.get('base', 'N/A')}\n"
        f"• Description: {data.get('description', 'N/A')}\n"
        f"• Quote Currency: {data.get('quote_currency', 'N/A')}"
    )

def format_time_data(data: list, data_type: str) -> str:
    """Format time series data"""
    if not data:
        return "❌ No time series data available"
    
    lines = [f"📊 *{'OHLC' if data_type == 'ohlc' else 'Time Series'} Data*"]
    for item in data[:10]:  # Limit to 10 entries
        ts = item.get('time', item.get('timestamp', 0))
        dt = datetime.fromtimestamp(ts, UTC).strftime("%Y-%m-%d %H:%M")
        values = " | ".join([f"{k}: {v}" for k, v in item.items() if k != "time"])
        lines.append(f"• {dt}: {values}")
    
    return "\n".join(lines)

async def show_followup_menu(update: Update):
    """Show Pyth follow-up options"""
    await update.message.reply_text(
        "What would you like to do next?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ New Query", callback_data="menu_pyth"),
             InlineKeyboardButton("🏠 Main Menu", callback_data="menu_start")]
        ])
    )

async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Pyth cancellation"""
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    USER_STATE.pop(uid, None)
    
    await query.message.edit_text(
        "❌ Pyth query cancelled",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Try Again", callback_data="menu_pyth"),
             InlineKeyboardButton("🏠 Main Menu", callback_data="menu_start")]
        ])
    )

handlers = [
    CallbackQueryHandler(start_pyth, pattern="^menu_pyth$"),
    CallbackQueryHandler(pyth_callback, pattern="^pyth_"),
    CallbackQueryHandler(cancel_operation, pattern="^cancel_operation$"),
    MessageHandler(
        filters.TEXT & ~filters.COMMAND & (
            filters.Regex(r"^[\w-]{20,50}$") |  # ID format
            filters.Regex(r"^[\w-]+\s+[\w\d]+\s+\d+\s+\d+$")  # Parameter format
        ),
        handle_pyth_input
    )
]