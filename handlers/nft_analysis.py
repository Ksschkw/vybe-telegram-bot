# handlers/nft_analysis.py
import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, ContextTypes
from handlers.state import USER_STATE, CANCEL_BUTTON
import matplotlib.pyplot as plt
from io import BytesIO
from collections import defaultdict

def chunk_message(text: str, size: int = 4096) -> list:
    return [text[i:i+size] for i in range(0, len(text), size)]

async def fetch_nft_owners(collection_address: str) -> list:
    """Fetch NFT collection owners from Vybe API"""
    url = f"https://api.vybenetwork.xyz/nft/collection-owners/{collection_address}"
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
        print(f"Error fetching NFT owners: {e}")
        return []

def analyze_nft_distribution(owners: list) -> dict:
    """Analyze NFT ownership distribution"""
    distribution = defaultdict(int)
    for owner in owners:
        address = owner.get("address", "unknown")
        distribution[address] += 1
    return dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))

def generate_distribution_chart(distribution: dict) -> BytesIO:
    """Generate ownership distribution chart"""
    top_holders = list(distribution.items())[:10]
    labels = [f"{addr[:3]}..{addr[-3]}" for addr, _ in top_holders]
    counts = [count for _, count in top_holders]

    plt.figure(figsize=(10, 5))
    plt.barh(labels, counts, color='purple')
    plt.xlabel('Number of NFTs')
    plt.title('Top 10 NFT Holders')
    plt.gca().invert_yaxis()
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf

async def start_nft(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiate NFT analysis flow"""
    await update.callback_query.answer()
    USER_STATE[update.effective_user.id] = {"flow": "nft", "step": "input"}
    
    await update.callback_query.message.reply_text(
        "🖼 *NFT Collection Analysis*\nSend collection address:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(CANCEL_BUTTON)
    )

async def handle_nft_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process NFT collection address input"""
    uid = update.effective_user.id
    state = USER_STATE.get(uid, {})
    
    if state.get("flow") != "nft":
        return
    
    collection_address = update.message.text.strip()
    
    try:
        # Validate address format
        if not collection_address.isalnum() or len(collection_address) not in [32, 44]:
            raise ValueError("Invalid collection address format")
            
        owners = await fetch_nft_owners(collection_address)
        if not owners:
            raise ValueError("No owners found for this collection")
            
        distribution = analyze_nft_distribution(owners)
        chart_image = generate_distribution_chart(distribution)
        
        # Build response message
        total_owners = len(distribution)
        total_nfts = sum(distribution.values())
        top_holder = next(iter(distribution.items()), None)
        
        response = (
            f"🖼 *NFT Collection Analysis*\n\n"
            f"🔗 Collection: `{collection_address[:6]}...{collection_address[-4:]}`\n"
            f"👥 Unique Owners: {total_owners}\n"
            f"📦 Total NFTs: {total_nfts}\n"
            f"🏆 Top Holder: {top_holder[1] if top_holder else 0} NFTs\n\n"
            f"[View on Vybe](https://alpha.vybenetwork.com/nft/{collection_address})"
        )
        
        # Send results
        await update.message.reply_photo(
            photo=chart_image,
            caption=response,
            parse_mode="Markdown"
        )
        
        # Send top holders list
        top_holders = "\n".join(
            [f"{i+1}. `{addr}`: {count} NFTs" 
             for i, (addr, count) in enumerate(list(distribution.items())[:5])]
        )
        await update.message.reply_text(
            f"🏅 *Top Holders*\n{top_holders}",
            parse_mode="Markdown"
        )
        
    except ValueError as e:
        await update.message.reply_text(
            f"❌ {str(e)}. Please try again:",
            reply_markup=InlineKeyboardMarkup(CANCEL_BUTTON)
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error analyzing collection: {str(e)}",
            reply_markup=InlineKeyboardMarkup(CANCEL_BUTTON)
        )
    finally:
        USER_STATE.pop(uid, None)
        await show_followup_menu(update)

async def show_followup_menu(update: Update):
    """Show navigation options after analysis"""
    await update.message.reply_text(
        "What would you like to do next?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🖼 New Analysis", callback_data="menu_nft"),
             InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
    )

async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle NFT analysis cancellation"""
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    USER_STATE.pop(uid, None)
    
    await query.message.edit_text(
        "❌ NFT analysis cancelled",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🖼 Try Again", callback_data="menu_nft"),
             InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ])
    )

handlers = [
    CallbackQueryHandler(start_nft, pattern="^menu_nft$"),
    CallbackQueryHandler(cancel_operation, pattern="^cancel_operation$"),
    MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$'),
        handle_nft_input
    )
]