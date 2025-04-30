import requests, json, aiohttp
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes

USER_STATE = {}

def chunk_message(text: str, size: int = 4096):
    return [text[i : i + size] for i in range(0, len(text), size)]

async def get_token_price(token_mint=None, count=10):
    url = "https://api.vybenetwork.xyz/tokens"
    headers = {"accept":"application/json","X-API-KEY":__import__('os').getenv("VYBE_API_KEY")}
    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers=headers) as r:
            data = await r.json()
    toks = data.get("data",[])
    if token_mint:
        toks = [t for t in toks if t.get("mintAddress")==token_mint]
    return toks[:count]

async def start_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    USER_STATE[update.effective_user.id]={"flow":"prices","step":None}
    kb = [
        [InlineKeyboardButton("Top Tokens", callback_data="prices_top")],
        [InlineKeyboardButton("Single Token", callback_data="prices_single")],
    ]
    await update.callback_query.message.reply_text(
        "📊 *Prices Menu*",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

async def prices_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id; action=q.data.split("_")[1]
    USER_STATE[uid]["step"]=action
    prompt = "🔢 Send number of top tokens:" if action=="top" else "🔎 Send token mint:"
    await q.message.reply_text(prompt)

async def handle_prices_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    state=USER_STATE.get(uid)
    if not state or state["flow"]!="prices": return

    step=state["step"]; txt=update.message.text.strip()
    if step=="top":
        try:
            n=int(txt)
            toks=await get_token_price(count=n)
            msg="\n".join(f"{t['symbol']}: ${t['price']}" for t in toks)
            await update.message.reply_text(msg, parse_mode="Markdown")
        except:
            await update.message.reply_text("❌ Invalid number.")
    else:
        toks=await get_token_price(token_mint=txt, count=1)
        if not toks:
            await update.message.reply_text("⚠️ Token not found.")
        else:
            t=toks[0]
            await update.message.reply_text(
                f"🏷️ *{t['symbol']}* — {t['name']}\n💵 ${t['price']}",
                parse_mode="Markdown"
            )
    USER_STATE.pop(uid)

handlers = [
    CallbackQueryHandler(prices_callback, pattern="^prices_"),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prices_input)
]
