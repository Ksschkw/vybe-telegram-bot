import time, aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes

USER_STATE = {}

async def fetch_ohlcv(mint,res,start,end):
    url=f"https://api.vybenetwork.xyz/price/{mint}/token-ohlcv"
    headers={"accept":"application/json","X-API-KEY":__import__('os').getenv("VYBE_API_KEY")}
    params={"resolution":res,"timeStart":start,"timeEnd":end}
    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers=headers, params=params) as r:
            return (await r.json()).get("data",[])

async def start_pyth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    USER_STATE[update.effective_user.id]={"flow":"pyth","step":None}
    kb=[
      [InlineKeyboardButton("1h",callback_data="pyth_1h")],
      [InlineKeyboardButton("4h",callback_data="pyth_4h")],
      [InlineKeyboardButton("1d",callback_data="pyth_1d")],
    ]
    await update.callback_query.message.reply_text(
        "⚙️ *Pyth Menu*",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

async def pyth_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    USER_STATE[q.from_user.id]["step"]=q.data.split("_")[1]
    await q.message.reply_text("🔎 Send token mint:")

async def handle_pyth_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    state=USER_STATE.get(uid)
    if not state or state["flow"]!="pyth": return

    res=state["step"]; mint=update.message.text.strip()
    now=int(time.time()); delta={"1h":3600,"4h":14400,"1d":86400}[res]
    data=await fetch_ohlcv(mint,res,now-delta,now)
    text="\n".join(f"{d['time']} O:{d['open']} H:{d['high']} L:{d['low']} C:{d['close']}" for d in data)
    await update.message.reply_text(text, parse_mode="Markdown")
    USER_STATE.pop(uid)

handlers = [
    CallbackQueryHandler(pyth_callback, pattern="^pyth_"),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pyth_input)
]
