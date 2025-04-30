import time, aiohttp
from datetime import datetime, UTC
import matplotlib, matplotlib.pyplot as plt, matplotlib.dates as mdates
from io import BytesIO
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes

USER_STATE = {}

async def fetch_ohlcv(mint, res, start, end):
    url = f"https://api.vybenetwork.xyz/price/{mint}/token-ohlcv"
    headers = {"accept":"application/json","X-API-KEY":__import__('os').getenv("VYBE_API_KEY")}
    params={"resolution":res,"timeStart":start,"timeEnd":end}
    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers=headers, params=params) as r:
            return (await r.json()).get("data",[])

async def start_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    USER_STATE[update.effective_user.id]={"flow":"chart","step":None}
    kb=[
      [InlineKeyboardButton("7d",callback_data="chart_7d")],
      [InlineKeyboardButton("30d",callback_data="chart_30d")],
    ]
    await update.callback_query.message.reply_text(
        "📈 *Chart Menu*",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

async def chart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id; USER_STATE[uid]["step"]=q.data.split("_")[1]
    await q.message.reply_text("🔎 Send token mint:")

async def handle_chart_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    state=USER_STATE.get(uid)
    if not state or state["flow"]!="chart": return

    mint=update.message.text.strip()
    days = 7 if state["step"]=="7d" else 30
    end=int(time.time()); start=end-days*86400
    data = await fetch_ohlcv(mint,"1d",start,end)
    dates=[datetime.fromtimestamp(o['time'],tz=UTC) for o in data]
    closes=[o['close'] for o in data]

    plt.figure(figsize=(6,3))
    plt.plot(dates,closes)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    buf=BytesIO(); plt.savefig(buf,format='png',bbox_inches='tight'); buf.seek(0); plt.close()
    await update.message.reply_photo(buf)
    USER_STATE.pop(uid)

handlers = [
    CallbackQueryHandler(chart_callback, pattern="^chart_"),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chart_input)
]
