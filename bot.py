from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import utils
import os
from dotenv import load_dotenv
from datetime import datetime
import time
import aiohttp



load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
VYBE_API_KEY = os.getenv("VYBE_API_KEY")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Vybe Analytics Bot Activated!\n\n"
                               "📋 Available commands:\n"
                               "🔍 /balance <wallet> - Check wallet balance\n"
                               "📊 /prices <token_mint(optional)> [token count(optional)]- Get token prices\n"
                               "🐋 /whalealert <threshold(optional)> [alert count(optional)] - Latest large transactions\n"
                               "🔎 /tokendetails <mintAdress> - Get token details\n"
                               "👑 /topholders <mintAdress> [count(optional)] - View top holders of a token\n"
                               "📊 /chart <mint_address> - get the price chart.\n"
                               "🖼 /nft_stats <collection_address> - Get NFT collection statistics\n"
                               )
    
async def token_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /tokendetails command"""
    if not context.args:
        await update.message.reply_text("⚠️ Please provide a token mint address\nExample: /tokenDetails EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
        return
    
    token_mint = context.args[0]
    token_info = await utils.get_token_details(token_mint)
    await update.message.reply_text(token_info)
async def get_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet_address = context.args[0] if context.args else None
    if not wallet_address:
        await update.message.reply_text("Please provide a wallet address")
        return
    
    balance = await utils.get_wallet_balance(wallet_address)
    await update.message.reply_text(f"💰 Wallet Balance:\n{balance} SOL")

async def whale_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the whale alert command with optional parameters:
    - threshold: minimum USD value to consider a transfer as a whale transfer (default is 1000)
    - count: maximum number of alerts to display (default is 7)
    
    Usage Examples:
      /whalealert                -> Uses default threshold 1000 USD and displays up to 7 alerts.
      /whalealert 500            -> Uses threshold 500 USD and displays up to 7 alerts.
      /whalealert 500 3          -> Uses threshold 500 USD and displays up to 3 alerts.
    """
    try:
        # Parse the threshold; default to 1000 if not provided.
        threshold = float(context.args[0]) if len(context.args) > 0 else 1000
        # Parse the number of alerts to display; default to 7 if not provided.
        alert_count = int(context.args[1]) if len(context.args) > 1 else 7
        
        # Fetch whale transfers asynchronously.
        alerts = await utils.detect_whale_transfers(cap=threshold)
        
        # Slice the list to only include the desired number of alerts (or all that are available)
        alerts = alerts[:alert_count]
        if alerts:
            message = f"🔔 Whale Transfers (> {threshold} USD):\n\n"
            for transfer in alerts:
                    # Convert blockTime to human-readable format
                block_time = transfer.get('blockTime')
                if block_time:
                    readable_time = datetime.fromtimestamp(block_time).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    readable_time = 'N/A'
                message += (
                    f"🔑 Signature: {transfer.get('signature', 'N/A')}\n"
                    f"📤 Sender: {transfer.get('senderAddress', 'N/A')}\n"
                    f"📥 Receiver: {transfer.get('receiverAddress', 'N/A')}\n"
                    f"💰 Amount (raw): {transfer.get('amount', 'N/A')}\n"
                    f"🔢 Calculated Amount: {transfer.get('calculatedAmount', 'N/A')}\n"
                    f"💵 Value (USD): {transfer.get('valueUsd', 'N/A')}\n"
                    f"⏰ Block Time: {readable_time}\n\n"
                )
        else:
            message = "No whale transfers found exceeding the threshold."

        
        # If the message exceeds Telegram's character limit, split it into chunks.
        for chunk in utils.chunk_message(message):
            await update.message.reply_text(chunk)
    
    except ValueError:
        await update.message.reply_text("❌ Invalid input. Usage: /whalealert <threshold> [alert count]")

async def send_chunks(update: Update, text: str, chunk_size: int = 4096):
    """Send text in Telegram message chunks if it's too long."""
    for chunk in utils.chunk_message(text, chunk_size):
        await update.message.reply_text(chunk)

async def check_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /prices command.

    Usage:
      /prices                -> Displays 10 tokens (default)
      /prices 15             -> Displays 15 tokens
      /prices <token_mint>   -> Displays details for the specified token
    """
    # If no arguments, show default 10 tokens.
    if not context.args:
        price_info = await utils.get_token_price(count=10)
        await send_chunks(update, price_info)
        return

    # If the first argument is a number, treat it as the desired count.
    try:
        count = int(context.args[0])
        price_info = await utils.get_token_price(count=count)
        await send_chunks(update, price_info)
    except ValueError:
        # Otherwise, assume the argument is a token mint address.
        token_mint = context.args[0]
        price_info = await utils.get_token_price(token_mint=token_mint)
        await send_chunks(update, price_info)

async def top_token_holders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 1:
            await update.message.reply_text("❌ Usage: /topholders <mintAddress> [count]")
            return

        mint_address = context.args[0]
        count = int(context.args[1]) if len(context.args) > 1 else 10

        holders = await utils.get_top_token_holders(mint_address, count)

        if not holders:
            await update.message.reply_text("😕 No data found for this token.")
            return

        # message = f"👑 *Top {count} Holders of Token:* `{mint_address}`\n\n"
        token_symbol = holders[0].get("tokenSymbol", "N/A")
        message = f"👑 *Top {count} Holders of Token:* `{mint_address}` — *{token_symbol}*\n\n"

        for holder in holders:
            message += (
                f"🏅 Rank: {holder.get('rank', 'N/A')}\n"
                f"🧾 Name: {holder.get('ownerName') or 'N/A'}\n"
                f"📦 Address: `{holder.get('ownerAddress')}`\n"
                f"💰 Balance: {holder.get('balance', 'N/A')}\n"
                f"💵 USD Value: ${float(holder.get('valueUsd', 0)):.2f}\n"
                f"📈 % Supply Held: {holder.get('percentageOfSupplyHeld', 0):.4f}%\n\n"
            )

        for chunk in utils.chunk_message(message):
            await update.message.reply_text(chunk, parse_mode="Markdown")

    except Exception as e:
        print(f"Error in /topholders: {e}")
        await update.message.reply_text("❌ An error occurred while fetching top holders.")

async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /chart <mint_address>")
        return

    mint_address = context.args[0]
    resolution = '1d'  # Daily data points
    time_end = int(time.time())
    time_start = time_end - (30 * 24 * 60 * 60)  # Last 30 days

    try:
        ohlcv_data = await utils.fetch_ohlcv_data(mint_address, resolution, time_start, time_end)
        if not ohlcv_data:
            await update.message.reply_text("No data available for the provided mint address.")
            return

        chart_image = await utils.generate_price_chart(ohlcv_data)
        await update.message.reply_photo(photo=chart_image)
    except aiohttp.ClientResponseError as e:
        await update.message.reply_text(f"Failed to fetch data: {e}")
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")
    
# NFT Collection Statistics
async def nft_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Fetch the NFT collection owners
    collection_address = context.args[0] if context.args else None
    owners_data = await utils.fetch_nft_collection_owners(collection_address)
    
    if owners_data is None:
        await update.message.reply_text("😕Failed to retrieve data. Please check the collection address.")
        return
    
    # Analyze the data
    owners = owners_data.get('owners', [])
    stats = utils.analyze_nft_owners(owners)
    
    # Format the response
    response = (
        f"NFT Collection Statistics for {collection_address}:\n"
        f"Total Unique Owners: {stats['total_owners']}\n"
        f"Concentration of Holdings:\n"
    )
    
    for owner, count in stats['concentration'].items():
        response += f"- {owner}: {count} NFTs\n"
    
    await update.message.reply_text(response)

# REALTIME / WEBSOCKET 


if __name__ == "__main__":
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", get_balance))
    app.add_handler(CommandHandler("whalealert", whale_alert))
    app.add_handler(CommandHandler("prices", check_prices))
    app.add_handler(CommandHandler("tokenDetails", token_details))
    app.add_handler(CommandHandler("topholders", top_token_holders))
    app.add_handler(CommandHandler("chart", chart))
    app.add_handler(CommandHandler("nft_stats", nft_stats))


    
    # Start polling
    app.run_polling()