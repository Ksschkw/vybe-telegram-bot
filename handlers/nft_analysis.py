import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes

USER_STATE = {}

async def fetch_nft_owners(coll):
    url=f"https://api.vybenetwork.xyz/nft/collection-owners/{coll}"
    headers={"accept":"application/json","X-API-KEY":__import__('os').getenv("VYBE_API_KEY")}
    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers=headers) as r:
            return (await r.json()).get("data",[])

async def start_nft(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    USER_STATE[update.effective_user.id]={"flow":"nft","step":"analyze"}
    kb=[[InlineKeyboardButton("Analyze",callback_data="nft_analyze")]]
    await update.callback_query.message.reply_text(
        "🖼 *NFT Menu*",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

async def nft_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query; await q.answer()
    await q.message.reply_text("🔗 Send collection address:")

async def handle_nft_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if USER_STATE.get(update.effective_user.id,{}).get("flow")!="nft": return
    coll=update.message.text.strip()
    owners=await fetch_nft_owners(coll)
    total=len(owners); uniq=len({o['address'] for o in owners})
    report=f"🖼 `{coll}`\nTotal NFTs: {total}\nUnique owners: {uniq}"
    await update.message.reply_text(report, parse_mode="Markdown")
    USER_STATE.pop(update.effective_user.id)

handlers = [
    CallbackQueryHandler(nft_callback, pattern="^nft_"),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_nft_input)
]
