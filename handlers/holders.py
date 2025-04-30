import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes

USER_STATE = {}

async def get_top_holders(mint, count):
    url=f"https://api.vybenetwork.xyz/token/{mint}/top-holders"
    headers={"accept":"application/json","X-API-KEY":__import__('os').getenv("VYBE_API_KEY")}
    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers=headers) as r:
            return (await r.json()).get("data",[])[:count]

async def start_holders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    USER_STATE[update.effective_user.id]={"flow":"holders","step":None}
    kb=[[InlineKeyboardButton("Top Holders",callback_data="holders_top")]]
    await update.callback_query.message.reply_text(
        "👑 *Holders Menu*",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

async def holders_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    uid=q.from_user.id; USER_STATE[uid]["step"]="top"
    await q.message.reply_text("🔢 Send `<mint> <count>`:")

async def handle_holders_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    state=USER_STATE.get(uid)
    if not state or state["flow"]!="holders": return

    parts=update.message.text.strip().split()
    if len(parts)!=2:
        await update.message.reply_text("❌ Usage: `<mint> <count>`")
    else:
        mint,count=parts[0],int(parts[1])
        hs=await get_top_holders(mint,count)
        msg="\n".join(f"{i+1}. `{h['ownerAddress']}` — {h['balance']}" for i,h in enumerate(hs))
        await update.message.reply_text(msg, parse_mode="Markdown")
    USER_STATE.pop(uid)

handlers = [
    CallbackQueryHandler(holders_callback, pattern="^holders_"),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_holders_input)
]
