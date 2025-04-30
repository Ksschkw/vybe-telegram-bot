import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes

# per-user flow state
USER_STATE = {}

def chunk_message(text: str, size: int = 4096):
    return [text[i : i + size] for i in range(0, len(text), size)]

async def fetch_nft_owners(collection_address: str) -> list:
    """Fetch up to 1000 owners of an NFT collection."""
    url = f"https://api.vybenetwork.xyz/nft/collection-owners/{collection_address}"
    headers = {
        "accept": "application/json",
        "X-API-KEY": __import__("os").getenv("VYBE_API_KEY"),
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
    # endpoint returns { data: [ { address, ... }, ... ] }
    return data.get("data", [])

async def start_nft(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the NFT menu (just one option)."""
    await update.callback_query.answer()
    USER_STATE[update.effective_user.id] = {"flow": "nft", "step": "analyze"}
    kb = [[InlineKeyboardButton("Analyze Collection", callback_data="nft_analyze")]]
    await update.callback_query.message.reply_text(
        "🖼 *NFT Analytics Menu*\n\n"
        "Press *Analyze Collection* then send the collection address to see owner stats.",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown",
    )

async def nft_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt the user for the collection address."""
    q = update.callback_query
    await q.answer()
    await q.message.reply_text("🔗 Send the NFT collection address:")

async def handle_nft_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch and display the list of owners for the given collection."""
    uid = update.effective_user.id
    state = USER_STATE.get(uid)
    if not state or state.get("flow") != "nft":
        return

    collection = update.message.text.strip()
    try:
        owners = await fetch_nft_owners(collection)
        if not owners:
            await update.message.reply_text("🖼 No owners found for that collection.")
        else:
            lines = [f"🖼 *Owners of `{collection}`* (showing {len(owners)}):"]
            for i, owner in enumerate(owners, start=1):
                addr = owner.get("address", "N/A")
                lines.append(f"{i}. `{addr}`")
            text = "\n".join(lines)
            for chunk in chunk_message(text):
                await update.message.reply_text(chunk, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error fetching NFT owners: {e}")

    USER_STATE.pop(uid)

handlers = [
    CallbackQueryHandler(nft_callback, pattern="^nft_"),
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_nft_input),
]
