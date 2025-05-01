import aiohttp
import re
from datetime import datetime, timedelta, UTC
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
                data = await resp.json()
                logger.debug(f"fetch_pyth_data: Fetched {endpoint} for {identifier} with params {params}: {data}")
                return data
    except Exception as e:
        logger.error(f"Pyth API Error ({endpoint}, {identifier}, params={params}): {e}")
        return {}

async def start_pyth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiate Pyth oracle menu"""
    await update.callback_query.answer()
    USER_STATE[update.effective_user.id] = {"flow": "pyth", "step": "menu"}
    
    keyboard = [
        [InlineKeyboardButton("Price Feed", callback_data="pyth_price"),
         InlineKeyboardButton("Hourly Summary", callback_data="pyth_ohlc")],
        [InlineKeyboardButton("Price Updates", callback_data="pyth_ts")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]
    ]
    
    await update.callback_query.message.reply_text(
        "⚙️ *Price Oracle Menu*\nChoose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def pyth_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle data type selection"""
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
        "price": "🔎 Enter the Price Feed Code (e.g., JBu1AL4obBcCMqKBBxhpWCNUt136ijcuMZLFvTP7iWdB):",
        "ohlc": "📝 Format: <FeedID> <Interval> <Start> <End>\nExample: `JBu1AL4obBcCMqKBBxhpWCNUt136ijcuMZLFvTP7iWdB hourly 2025-04-24 2025-04-30`",
        "ts": "📝 Format: <FeedID> <Interval> <Start> <End>\nExample: `JBu1AL4obBcCMqKBBxhpWCNUt136ijcuMZLFvTP7iWdB every 4 hours 2025-04-24 2025-04-30`"
    }
    
    await q.message.edit_text(
        prompts[data_type],
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(CANCEL_BUTTON)
    )

def parse_time_input(time_str: str) -> int:
    """Convert YYYY-MM-DD to Unix timestamp"""
    time_str = time_str.strip()
    
    # Validate YYYY-MM-DD format
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', time_str):
        raise ValueError("Invalid date format. Use YYYY-MM-DD (e.g., 2025-04-24)")
    
    try:
        dt = datetime.strptime(time_str, '%Y-%m-%d').replace(tzinfo=UTC)
        return int(dt.timestamp())
    except ValueError:
        raise ValueError("Invalid date. Use YYYY-MM-DD (e.g., 2025-04-24)")

async def handle_pyth_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process Pyth data input"""
    uid = update.effective_user.id
    state = USER_STATE.get(uid, {})
    
    logger.debug(f"handle_pyth_input: User {uid}, state: {state}, input: '{update.message.text}'")
    
    if state.get("flow") != "pyth":
        logger.debug(f"handle_pyth_input: Skipping, not in pyth flow for user {uid}")
        return False  # Allow other handlers to process
    
    text = update.message.text.strip()
    data_type = state["type"]
    
    try:
        if data_type == "price":
            # Validate ID as Solana public key (32-44 base58 characters)
            if not (32 <= len(text) <= 44 and all(c in "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz" for c in text)):
                raise ValueError("Invalid Price Feed Code. Use a valid code (32-44 characters).")
                
            # Simple ID-based lookup
            result = await fetch_pyth_data(endpoint="pyth-price", identifier=text)
            if not result:
                raise ValueError("No data returned from API")
            response = format_simple_result(result, data_type)
            
        else:
            # OHLC/TS requires parameters parsing
            pattern = r'^\s*([1-9A-HJ-NP-Za-km-z]{32,44})\s+(hourly|every\s+4\s+hours|daily|every\s+minute|every\s+5\s+minutes|every\s+15\s+minutes|every\s+30\s+minutes)\s+(\d{4}-\d{2}-\d{2})\s+(\d{4}-\d{2}-\d{2})$'
            match = re.match(pattern, text, re.IGNORECASE)
            if not match:
                raise ValueError("Invalid format. Use: FeedID Interval YYYY-MM-DD YYYY-MM-DD (e.g., JBu1AL4obBcCMqKBBxhpWCNUt136ijcuMZLFvTP7iWdB hourly 2025-04-24 2025-04-30)")
                
            feed_id, resolution, start, end = match.groups()
            logger.debug(f"Parsed input: feed_id={feed_id}, resolution={resolution}, start={start}, end={end}")
            
            # Validate FeedID
            if not (32 <= len(feed_id) <= 44 and all(c in "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz" for c in feed_id)):
                raise ValueError("Invalid FeedID. Use a valid Price Feed Code.")
            
            # Validate and map resolution
            resolution_map = {
                "hourly": "1h",
                "every 4 hours": "4h",
                "daily": "1d",
                "every minute": "1m",
                "every 5 minutes": "5m",
                "every 15 minutes": "15m",
                "every 30 minutes": "30m"
            }
            resolution = resolution.lower().strip()
            if resolution not in resolution_map:
                raise ValueError("Invalid interval. Use: hourly, every 4 hours, daily, every minute, every 5 minutes, every 15 minutes, every 30 minutes")
            api_resolution = resolution_map[resolution]
            
            # Parse start and end times
            time_start = parse_time_input(start)
            time_end = parse_time_input(end)
            
            # Validate timestamps
            if time_end <= time_start:
                raise ValueError("End date must be after Start date")
            if time_start < 1609459200:  # Jan 1, 2021
                raise ValueError("Start date is too far in the past (before 2021)")
                
            params = {
                "resolution": api_resolution,
                "timeStart": time_start,
                "timeEnd": time_end
            }
            
            endpoint = "pyth-price-ohlc" if data_type == "ohlc" else "pyth-price-ts"
            data = await fetch_pyth_data(endpoint, feed_id, params)
            if not data or not data.get("data"):
                raise ValueError("No data available for the specified time range")
            response = format_time_data(data, data_type)
            
        # Send response in chunks
        for chunk in chunk_message(response):
            await update.message.reply_text(chunk, parse_mode="Markdown")
            
    except ValueError as e:
        error_msg = f"❌ Invalid input: {str(e)}\nPlease try again:"
        logger.error(f"handle_pyth_input: ValueError for user {uid}: {str(e)}")
        await update.message.reply_text(error_msg, reply_markup=InlineKeyboardMarkup(CANCEL_BUTTON))
        return True  # Stop propagation
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}\nPlease try again:"
        logger.error(f"handle_pyth_input: Error for user {uid}: {str(e)}")
        await update.message.reply_text(error_msg, reply_markup=InlineKeyboardMarkup(CANCEL_BUTTON))
        return True  # Stop propagation
    finally:
        USER_STATE.pop(uid, None)
        await show_followup_menu(update)
        logger.info(f"handle_pyth_input: User {uid} stopping propagation")
        return True  # Stop propagation

def format_simple_result(data: dict, data_type: str) -> str:
    """Format simple price response"""
    if not data:
        return "❌ No data found"
    
    if data_type == "price":
        price = round(float(data.get('price', 0)), 2)
        confidence = round(float(data.get('confidence', 0)), 2)
        timestamp = datetime.fromtimestamp(data.get('lastUpdated', 0), UTC).strftime("%b %d, %Y %I:%M %p")
        return (
            f"📈 *Current Price*\n\n"
            f"• Price: ${price}\n"
            f"• Price Range: ±${confidence}\n"
            f"• Updated: {timestamp}"
        )
    return "❌ Invalid data type"

def format_time_data(data: dict, data_type: str) -> str:
    """Format time series data"""
    data_list = data.get('data', [])
    if not data_list:
        return "❌ No time series data available"
    
    if data_type == "ohlc":
        lines = [f"📊 *Hourly Price Summary ({datetime.fromtimestamp(data_list[0].get('timeBucketStart', 0), UTC).strftime('%b %d, %Y')})*"]
        for item in data_list[:10]:
            ts = item.get('timeBucketStart', 0)
            dt = datetime.fromtimestamp(ts, UTC).strftime("%I:%M %p")
            open_price = round(float(item.get('open', 0)), 2)
            high_price = round(float(item.get('high', 0)), 2)
            low_price = round(float(item.get('low', 0)), 2)
            close_price = round(float(item.get('close', 0)), 2)
            avg_price = round(float(item.get('avgPrice', 0)), 2)
            avg_conf = round(float(item.get('avgConf', 0)), 2)
            lines.append(
                f"At {dt}:\n"
                f"• Starting Price: ${open_price}\n"
                f"• Highest Price: ${high_price}\n"
                f"• Lowest Price: ${low_price}\n"
                f"• Ending Price: ${close_price}\n"
                f"• Average Price: ${avg_price}\n"
                f"• Price Range: ±${avg_conf}"
            )
    else:  # ts
        lines = [f"📊 *Price Updates ({datetime.fromtimestamp(data_list[0].get('lastUpdated', 0), UTC).strftime('%b %d, %Y')})*"]
        for item in data_list[:10]:
            ts = item.get('lastUpdated', 0)
            dt = datetime.fromtimestamp(ts, UTC).strftime("%I:%M %p")
            price = round(float(item.get('price', 0)), 2)
            confidence = round(float(item.get('confidence', 0)), 2)
            lines.append(
                f"At {dt}:\n"
                f"• Price: ${price}\n"
                f"• Price Range: ±${confidence}"
            )
    
    return "\n\n".join(lines)

async def show_followup_menu(update: Update):
    """Show follow-up options"""
    await update.message.reply_text(
        "What would you like to do next?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ New Query", callback_data="menu_pyth"),
             InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
    )

async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancellation"""
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    USER_STATE.pop(uid, None)
    
    await query.message.edit_text(
        "❌ Query cancelled",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Try Again", callback_data="menu_pyth"),
             InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
    )

handlers = [
    CallbackQueryHandler(start_pyth, pattern="^menu_pyth$"),
    CallbackQueryHandler(pyth_callback, pattern="^pyth_"),
    CallbackQueryHandler(cancel_operation, pattern="^cancel_operation$"),
    MessageHandler(
        filters.TEXT & ~filters.COMMAND & (
            filters.Regex(r'^\s*[1-9A-HJ-NP-Za-km-z]{32,44}\s*$') |  # Solana public key
            filters.Regex(r'^\s*[1-9A-HJ-NP-Za-km-z]{32,44}\s+(hourly|every\s+4\s+hours|daily|every\s+minute|every\s+5\s+minutes|every\s+15\s+minutes|every\s+30\s+minutes)\s+\d{4}-\d{2}-\d{2}\s+\d{4}-\d{2}-\d{2}\s*$')  # FeedID Interval YYYY-MM-DD YYYY-MM-DD
        ),
        handle_pyth_input
    )
]