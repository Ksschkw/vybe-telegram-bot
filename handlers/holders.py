# handlers/holders.py
import aiohttp
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes
from handlers.state import USER_STATE, CANCEL_BUTTON

def chunk_message(text: str, size: int = 4096) -> list:
    return [text[i:i+size] for i in range(0, len(text), size)]

async def fetch_top_holders(mint: str, count: int) -> list:
    """Fetch top holders from Vybe API"""
    url = f"https://api.vybenetwork.xyz/token/{mint}/top-holders"
    headers = {
        "accept": "application/json",
        "X-API-KEY": __import__("os").getenv("VYBE_API_KEY"),
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("data", [])[:count]
    except Exception as e:
        print(f"Error fetching top holders: {e}")
        return []

async def fetch_holders_ts(mint: str) -> list:
    """Fetch holders time series data"""
    url = f"https://api.vybenetwork.xyz/token/{mint}/holders-ts"
    headers = {
        "accept": "application/json",
        "X-API-KEY": __import__("os").getenv("VYBE_API_KEY"),
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("data", [])
    except Exception as e:
        print(f"Error fetching holders TS: {e}")
        return []

async def start_holders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiate holders flow"""
    await update.callback_query.answer()
    USER_STATE[update.effective_user.id] = {"flow": "holders", "step": "menu"}
    
    keyboard = [
        [InlineKeyboardButton("Top Holders", callback_data="holders_top"),
         InlineKeyboardButton("Holders History", callback_data="holders_ts")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]
    ]
    
    await update.callback_query.message.edit_text(
        "👑 *Holders Analysis*\nSelect analysis type:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def holders_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle analysis type selection"""
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    analysis_type = q.data.split("_")[1]
    
    USER_STATE[uid] = {
        "flow": "holders",
        "step": "input",
        "type": analysis_type,
        "message_id": q.message.message_id
    }
    
    if analysis_type == "top":
        prompt = "🔢 Send `<mint_address> <count>`\nExample: `Grass... 10`"
    else:
        prompt = "🔎 Send token mint address:"
    
    await q.message.edit_text(
        prompt,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(CANCEL_BUTTON)
    )

async def handle_holders_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process holders input"""
    uid = update.effective_user.id
    state = USER_STATE.get(uid, {})
    
    if state.get("flow") != "holders":
        return
    
    text = update.message.text.strip()
    
    try:
        if state["type"] == "top":
            parts = text.split()
            if len(parts) != 2:
                raise ValueError("Need mint address and count")
                
            mint = parts[0]
            count = int(parts[1])
            if count < 1 or count > 25:
                raise ValueError("Count must be 1-25")
            
            holders = await fetch_top_holders(mint, count)
            response = format_top_holders(mint, holders)
            
        else:  # holders_ts
            mint = text
            series = await fetch_holders_ts(mint)
            response = format_holders_ts(mint, series)
            
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

def format_top_holders(mint: str, holders: list) -> str:
    """Format top holders response"""
    if not holders:
        return "👀 No holders found for this token"
    
    lines = [f"👑 Top {len(holders)} Holders of `{mint[:6]}...{mint[-4:]}`"]
    for i, holder in enumerate(holders, 1):
        addr = holder.get("ownerAddress", "N/A")
        balance = float(holder.get("balance", 0))
        usd = float(holder.get("valueUsd", 0))
        pct = float(holder.get("percentageOfSupplyHeld", 0))
        
        lines.append(
            f"{i}. `{addr}`\n"
            f"   Balance: {balance:.2f}\n"
            f"   Value: ${usd:,.2f}\n"
            f"   Supply %: {pct:.4f}%"
        )
    return "\n\n".join(lines)

def format_holders_ts(mint: str, series: list) -> str:
    """Format time series response"""
    if not series:
        return "📈 No historical data available"
    
    lines = [f"📈 Holders History for `{mint[:6]}...{mint[-4:]}`"]
    for point in series[:15]:  # Limit to 15 points
        ts = point.get("holdersTimestamp")
        dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else "N/A"
        count = point.get("nHolders", 0)
        lines.append(f"• {dt}: {count} holders")
    return "\n".join(lines)

async def show_followup_menu(update: Update):
    """Show navigation options after operation"""
    await update.message.reply_text(
        "What would you like to do next?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👑 New Analysis", callback_data="menu_holders")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_start")]
        ])
    )

async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle holders cancellation"""
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    USER_STATE.pop(uid, None)
    
    await query.message.edit_text(
        "❌ Holders analysis cancelled",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👑 Try Again", callback_data="menu_holders")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_start")]
        ])
    )

handlers = [
    CallbackQueryHandler(start_holders, pattern="^menu_holders$"),
    CallbackQueryHandler(holders_callback, pattern="^holders_"),
    CallbackQueryHandler(cancel_operation, pattern="^cancel_operation$"),
    MessageHandler(
        filters.TEXT & ~filters.COMMAND & (
            filters.Regex(r'^[1-9A-HJ-NP-Za-km-z]{32,44}\s+\d+$') |  # Mint + count
            filters.Regex(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')  # Mint only
        ),
        handle_holders_input
    )
]