# handlers/prices.py
import aiohttp
from datetime import datetime, UTC
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes
from handlers.state import USER_STATE, CANCEL_BUTTON

def chunk_message(text: str, size: int = 4096) -> list:
    return [text[i:i+size] for i in range(0, len(text), size)]

async def fetch_tokens(page: int = 1) -> list:
    """Fetch tokens from Vybe API with pagination"""
    url = "https://api.vybenetwork.xyz/tokens"
    headers = {
        "accept": "application/json",
        "X-API-KEY": __import__("os").getenv("VYBE_API_KEY"),
    }
    params = {"page": page}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("data", [])
    except Exception as e:
        print(f"Error fetching tokens: {e}")
        return []

async def fetch_token_details(mint: str) -> dict:
    """Fetch detailed information for a single token"""
    url = f"https://api.vybenetwork.xyz/token/{mint}"
    headers = {
        "accept": "application/json",
        "X-API-KEY": __import__("os").getenv("VYBE_API_KEY"),
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                resp.raise_for_status()
                return await resp.json()
    except Exception as e:
        print(f"Error fetching token details: {e}")
        return {}

async def start_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiate prices menu"""
    await update.callback_query.answer()
    USER_STATE[update.effective_user.id] = {"flow": "prices", "step": "menu"}
    
    keyboard = [
        [InlineKeyboardButton("Top Tokens", callback_data="prices_top"),
         InlineKeyboardButton("Token Details", callback_data="prices_single")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]
    ]
    
    await update.callback_query.message.reply_text(
        "📊 *Token Prices Menu*\nSelect analysis type:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def prices_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle prices submenu selection"""
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    analysis_type = q.data.split("_")[1]
    
    USER_STATE[uid] = {
        "flow": "prices",
        "step": "input",
        "type": analysis_type,
        "message_id": q.message.message_id
    }
    
    if analysis_type == "top":
        prompt = "🔢 How many tokens to display? (1-25)"
    else:
        prompt = "🔎 Send token mint address:"
    
    await q.message.edit_text(
        prompt,
        reply_markup=InlineKeyboardMarkup(CANCEL_BUTTON),
        parse_mode="Markdown"
    )

async def handle_prices_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process prices input"""
    uid = update.effective_user.id
    state = USER_STATE.get(uid, {})
    
    if state.get("flow") != "prices":
        return
    
    text = update.message.text.strip()
    
    try:
        if state["type"] == "top":
            if not text.isdigit():
                raise ValueError("Please enter a number")
            
            count = int(text)
            if count < 1 or count > 25:
                raise ValueError("Please enter between 1-25")
            
            tokens = await fetch_tokens()
            response = format_top_tokens(tokens[:count])
            
        else:
            mint = text
            details = await fetch_token_details(mint)
            response = format_token_details(mint, details)
            
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

def format_top_tokens(tokens: list) -> str:
    """Format top tokens response"""
    if not tokens:
        return "📊 No token data available"
    
    lines = ["📊 *Top Tokens*"]
    for i, token in enumerate(tokens, 1):
        symbol = token.get("symbol", "N/A")
        name = token.get("name", "N/A")
        price = float(token.get("price", 0))
        change_1d = float(token.get("price1d", 0)) * 100
        change_7d = float(token.get("price7d", 0)) * 100
        mcap = float(token.get("marketCap", 0))
        
        lines.append(
            f"{i}. *{symbol} - {name}*\n"
            f"   Price: ${price:.4f}\n"
            f"   24h: {change_1d:+.2f}% | 7d: {change_7d:+.2f}%\n"
            f"   Market Cap: ${mcap:,.0f}"
        )
    return "\n\n".join(lines)

def format_token_details(mint: str, details: dict) -> str:
    """Format single token details"""
    if not details:
        return f"❌ No details found for {mint[:6]}...{mint[-4:]}"
    
    symbol = details.get("symbol", "N/A")
    name = details.get("name", "N/A")
    price = float(details.get("price", 0))
    supply = int(details.get("currentSupply", 0))
    mcap = float(details.get("marketCap", 0))
    volume = float(details.get("usdValueVolume24h", 0))
    updated = datetime.fromtimestamp(details.get("updateTime", 0), UTC).strftime("%Y-%m-%d %H:%M")
    
    return (
        f"🔍 *{name} ({symbol})*\n\n"
        f"🏷 Mint: `{mint[:6]}...{mint[-4:]}`\n"
        f"💰 Price: ${price:.4f}\n"
        f"📈 24h Volume: ${volume:,.0f}\n"
        f"📦 Supply: {supply:,}\n"
        f"🏦 Market Cap: ${mcap:,.0f}\n"
        f"🕒 Updated: {updated} UTC\n\n"
        f"[View on Vybe](https://alpha.vybenetwork.com/tokens/{mint})"
    )

async def show_followup_menu(update: Update):
    """Show navigation options after operation"""
    await update.message.reply_text(
        "What would you like to do next?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 New Analysis", callback_data="menu_prices"),
             InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
    )

async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle prices cancellation"""
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    USER_STATE.pop(uid, None)
    
    await query.message.edit_text(
        "❌ Price analysis cancelled",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Try Again", callback_data="menu_prices"),
             InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
    )

handlers = [
    CallbackQueryHandler(start_prices, pattern="^menu_prices$"),
    CallbackQueryHandler(prices_callback, pattern="^prices_"),
    CallbackQueryHandler(cancel_operation, pattern="^cancel_operation$"),
    MessageHandler(
        filters.TEXT & ~filters.COMMAND & (
            filters.Regex(r"^\d+$") |  # Number input
            filters.Regex(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")  # Mint address
        ),
        handle_prices_input
    )
]