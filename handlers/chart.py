# handlers/chart.py
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime, UTC
from slashutils import fetch_ohlcv_data, generate_price_chart, get_token_name_for_chart
from handlers.state import USER_STATE, CANCEL_BUTTON
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def start_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiate chart flow"""
    query = update.callback_query
    await query.answer()
    uid = update.effective_user.id
    USER_STATE[uid] = {"flow": "chart", "step": "timeframe"}
    logger.info(f"start_chart: User {uid} initiated chart flow, state: {USER_STATE[uid]}")
    
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
    
    await query.message.reply_text(
        "📈 *Chart Settings*\nSelect timeframe:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def chart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle timeframe selection"""
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    choice = query.data.split("_")[1]
    
    USER_STATE[uid] = {
        "flow": "chart",
        "step": "input",
        "timeframe": choice,
        "message_id": query.message.message_id
    }
    logger.info(f"chart_callback: User {uid} selected {choice}, state: {USER_STATE[uid]}")
    
    if choice in ("7d", "30d"):
        prompt = "🔎 Send token mint address (e.g., Grass7B4RdKfBCjTKgSqnXkqjwiGvQyFbuSCUJr3XXjs):"
    else:
        prompt = "📅 Send start and end timestamps (e.g., `1633046400 1635724800`):"
    
    await query.message.edit_text(
        prompt,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(CANCEL_BUTTON)
    )

async def handle_chart_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process user input like /chart command"""
    uid = update.effective_user.id
    state = USER_STATE.get(uid, {})
    text = update.message.text.strip()
    
    logger.debug(f"handle_chart_input: User {uid}, state: {state}, input: '{text}'")
    
    if state.get("flow") != "chart":
        logger.debug(f"handle_chart_input: Skipping, not in chart flow for user {uid}")
        return False  # Allow other handlers to process
    
    try:
        if state["timeframe"] == "custom" and state.get("step") == "input":
            # Handle custom timestamp input
            parts = text.split()
            if len(parts) != 2 or not all(part.isdigit() for part in parts):
                raise ValueError("Invalid timestamp format, expected two numbers (e.g., '1633046400 1635724800')")
                
            start, end = sorted(map(int, parts))
            if end - start < 3600:
                raise ValueError("Minimum 1 hour range required")
                
            USER_STATE[uid].update({
                "start": start,
                "end": end,
                "step": "mint_input"
            })
            logger.info(f"handle_chart_input: User {uid} set custom timestamps, new state: {USER_STATE[uid]}")
            
            await update.message.reply_text(
                "🔎 Send token mint address (e.g., JBu1AL4obBcCMqKBBxhpWCNUt136ijcuMZLFvTP7iWdB):",
                reply_markup=InlineKeyboardMarkup(CANCEL_BUTTON)
            )
            return True  # Stop propagation
            
        elif state["timeframe"] in ("7d", "30d") and state.get("step") == "input":
            # Handle mint address
            mint_address = text
            if not (32 <= len(mint_address) <= 44 and all(c in "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz" for c in mint_address)):
                raise ValueError("Invalid mint address. Use 32-44 base58 characters (e.g., JBu1AL4obBcCMqKBBxhpWCNUt136ijcuMZLFvTP7iWdB)")
                
            days = 7 if state["timeframe"] == "7d" else 30
            resolution = "1d"
            time_end = int(time.time())
            time_start = time_end - (days * 24 * 60 * 60)
            
            logger.debug(f"handle_chart_input: User {uid} fetching OHLCV for mint {mint_address}, {days} days")
            ohlcv_data = await fetch_ohlcv_data(mint_address, resolution, time_start, time_end)
            if not ohlcv_data:
                logger.warning(f"handle_chart_input: No OHLCV data for mint {mint_address}")
                await update.message.reply_text("No data available for the provided mint address.")
                return True  # Stop propagation
                
            logger.debug(f"handle_chart_input: User {uid} generating chart for mint {mint_address}")
            chart_image = await generate_price_chart(ohlcv_data)
            if not chart_image:
                logger.error(f"handle_chart_input: Failed to generate chart for mint {mint_address}")
                raise ValueError("Failed to generate price chart")
                
            logger.debug(f"handle_chart_input: User {uid} fetching token name for mint {mint_address}")
            token_name = await get_token_name_for_chart(mint_address)
            if not token_name:
                token_name = "Unknown Token"
                logger.warning(f"handle_chart_input: No token name for mint {mint_address}")
                
            await update.message.reply_text(f"*{token_name}* 📈 Price Chart:", parse_mode="Markdown")
            await update.message.reply_photo(photo=chart_image)
            await update.message.reply_text(
                f"🔔 See more insights: https://alpha.vybenetwork.com/tokens/{mint_address}",
                parse_mode="Markdown"
            )
            
        elif state.get("step") == "mint_input":
            # Handle mint address after custom timestamps
            mint_address = text
            if not (32 <= len(mint_address) <= 44 and all(c in "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz" for c in mint_address)):
                raise ValueError("Invalid mint address. Use 32-44 base58 characters (e.g., JBu1AL4obBcCMqKBBxhpWCNUt136ijcuMZLFvTP7iWdB)")
                
            resolution = "1d"
            logger.debug(f"handle_chart_input: User {uid} fetching custom OHLCV for mint {mint_address}")
            ohlcv_data = await fetch_ohlcv_data(mint_address, resolution, state["start"], state["end"])
            if not ohlcv_data:
                logger.warning(f"handle_chart_input: No OHLCV data for mint {mint_address}")
                await update.message.reply_text("No data available for the provided mint address.")
                return True  # Stop propagation
                
            logger.debug(f"handle_chart_input: User {uid} generating custom chart for mint {mint_address}")
            chart_image = await generate_price_chart(ohlcv_data)
            if not chart_image:
                logger.error(f"handle_chart_input: Failed to generate custom chart for mint {mint_address}")
                raise ValueError("Failed to generate price chart")
                
            logger.debug(f"handle_chart_input: User {uid} fetching token name for mint {mint_address}")
            token_name = await get_token_name_for_chart(mint_address)
            if not token_name:
                token_name = "Unknown Token"
                logger.warning(f"handle_chart_input: No token name for mint {mint_address}")
                
            await update.message.reply_text(f"*{token_name}* 📈 Price Chart:", parse_mode="Markdown")
            await update.message.reply_photo(photo=chart_image)
            await update.message.reply_text(
                f"🔔 See more insights: https://alpha.vybenetwork.com/tokens/{mint_address}",
                parse_mode="Markdown"
            )
            
        # Reset state after successful chart generation
        logger.info(f"handle_chart_input: User {uid} chart generated, clearing state")
        USER_STATE.pop(uid, None)
        
        # Add follow-up actions
        await update.message.reply_text(
            "What would you like to do next?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 New Chart", callback_data="menu_chart")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
            ])
        )
        
        logger.info(f"handle_chart_input: User {uid} stopping propagation")
        return True  # Stop further handlers
        
    except Exception as e:
        logger.error(f"handle_chart_input: Error for user {uid}: {str(e)}")
        await update.message.reply_text(
            f"❌ Error: {str(e)}\nPlease try again:",
            reply_markup=InlineKeyboardMarkup(CANCEL_BUTTON)
        )
        logger.info(f"handle_chart_input: User {uid} stopping propagation on error")
        return True  # Stop propagation on error

async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle chart cancellation"""
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    logger.info(f"cancel_operation: User {uid} cancelled chart flow")
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