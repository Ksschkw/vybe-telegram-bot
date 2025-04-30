# handlers/accounts.py
import requests
import aiohttp
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes
from handlers.state import USER_STATE, CANCEL_BUTTON

def chunk_message(text: str, size: int = 4096) -> list:
    return [text[i:i+size] for i in range(0, len(text), size)]

async def fetch_known_accounts() -> list:
    """Fetch known accounts from Vybe API"""
    url = "https://api.vybenetwork.xyz/account/known-accounts"
    headers = {
        "accept": "application/json",
        "X-API-KEY": __import__("os").getenv("VYBE_API_KEY")
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("accounts", [])
    except Exception as e:
        print(f"Error fetching known accounts: {e}")
        return []

async def fetch_balance_ts(owner: str) -> list:
    """Fetch balance time series for a wallet"""
    url = f"https://api.vybenetwork.xyz/account/token-balance-ts/{owner}"
    headers = {
        "accept": "application/json",
        "X-API-KEY": __import__("os").getenv("VYBE_API_KEY")
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("data", [])
    except Exception as e:
        print(f"Error fetching balance time series: {e}")
        return []

async def get_wallet_balance(wallet_address: str) -> str:
    """Get formatted wallet balance"""
    url = f"https://api.vybenetwork.xyz/account/token-balance/{wallet_address}"
    headers = {
        "accept": "application/json",
        "X-API-KEY": __import__("os").getenv("VYBE_API_KEY")
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        ts = data.get('date')
        formatted_date = datetime.fromtimestamp(ts/1000).strftime('%Y-%m-%d %H:%M:%S') if ts else "Unknown"
        sol = float(data.get('stakedSolBalance', 0))
        total = int(data.get('totalTokenCount', 0))
        val = float(data.get('totalTokenValueUsd', 0))
        staked = float(data.get('activeStakedSolBalance', 0))

        return (
            f"💼 Wallet Overview\n\n"
            f"🔑 `{wallet_address[:6]}...{wallet_address[-4:]}`\n"
            f"🕒 Last Updated: {formatted_date}\n\n"
            f"💰 SOL: {sol:.4f}\n"
            f"📊 Tokens: {total:,}\n"
            f"💵 Value: ${val:.2f}\n"
            f"🔒 Staked SOL: {staked:.4f}"
        )
    except requests.exceptions.RequestException as e:
        return f"❌ Error fetching balance: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"

async def start_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show accounts menu with cancellation support"""
    await update.callback_query.answer()
    USER_STATE[update.effective_user.id] = {"flow": "accounts", "step": None}
    kb = [
        [InlineKeyboardButton("Known Accounts", callback_data="acct_known")],
        [InlineKeyboardButton("Wallet Balance", callback_data="acct_balance")],
        [InlineKeyboardButton("Balance History", callback_data="acct_balance_ts")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
    ]
    await update.callback_query.message.reply_text(
        "💼 *Accounts Menu*\nChoose an option:",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

async def accounts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle account submenu selection"""
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    action = q.data.split("_")[1]
    
    USER_STATE[uid] = {
        "flow": "accounts",
        "step": action,
        "message_id": q.message.message_id
    }
    
    if action == "known":
        await q.message.edit_text(
            "⏳ Fetching known accounts...",
            reply_markup=InlineKeyboardMarkup(CANCEL_BUTTON)
        )
        await handle_known_accounts(update, context)
    else:
        prompt_text = {
            "balance": "🔍 Send wallet address for balance:",
            "balance_ts": "📈 Send wallet address for history:"
        }[action]
        
        await q.message.edit_text(
            prompt_text,
            reply_markup=InlineKeyboardMarkup(CANCEL_BUTTON),
            parse_mode="Markdown"
        )

async def handle_known_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle known accounts display"""
    uid = update.callback_query.from_user.id
    try:
        accounts = await fetch_known_accounts()
        if not accounts:
            raise ValueError("No known accounts found")
            
        lines = ["🗒 *Known Accounts:*"]
        for i, acct in enumerate(accounts[:15], start=1):
            name = acct.get("name", "N/A")
            addr = acct.get("ownerAddress", "N/A")
            labels = ", ".join(acct.get("labels", [])) or "None"
            lines.append(f"{i}. *{name}* - `{addr}` ({labels})")
            
        await update.callback_query.message.edit_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="menu_accounts")]])
        )
    except Exception as e:
        await update.callback_query.message.edit_text(
            f"❌ Error: {str(e)}",
            reply_markup=InlineKeyboardMarkup(CANCEL_BUTTON)
        )
    finally:
        USER_STATE.pop(uid, None)

async def handle_accounts_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle wallet address input"""
    uid = update.effective_user.id
    state = USER_STATE.get(uid, {})
    
    if state.get("flow") != "accounts":
        return
        
    text = update.message.text.strip()
    
    try:
        if state.get("step") == "balance":
            balance_info = await get_wallet_balance(text)
            for chunk in chunk_message(balance_info):
                await update.message.reply_text(chunk, parse_mode="Markdown")
                
        elif state.get("step") == "balance_ts":
            series = await fetch_balance_ts(text)
            if not series:
                raise ValueError("No historical data found")
                
            lines = ["📈 *Balance History:*"]
            for point in series[:25]:
                ts = point.get("timestamp")
                dt = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M') if ts else "N/A"
                bal = point.get("balanceUsd", 0)
                lines.append(f"• {dt} - ${bal:.2f}")
                
            for chunk in chunk_message("\n".join(lines)):
                await update.message.reply_text(chunk, parse_mode="Markdown")
                
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error: {str(e)}",
            reply_markup=InlineKeyboardMarkup(CANCEL_BUTTON)
        )
    finally:
        USER_STATE.pop(uid, None)
        await update.message.reply_text(
            "What would you like to do next?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Accounts Menu", callback_data="menu_accounts")],
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
            ])
        )

async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancellation callback"""
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    USER_STATE.pop(uid, None)
    await query.message.edit_text(
        "❌ Operation cancelled",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Accounts Menu", callback_data="menu_accounts")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
    )

handlers = [
    CallbackQueryHandler(accounts_callback, pattern="^acct_"),
    CallbackQueryHandler(cancel_operation, pattern="^cancel_operation$"),
    MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$'),
        handle_accounts_input
    )
]