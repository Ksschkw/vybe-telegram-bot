from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup ,WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from handlers.state import *
import slashutils
import os
from dotenv import load_dotenv
from datetime import datetime
import logging
import time
import aiohttp

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
VYBE_API_KEY = os.getenv("VYBE_API_KEY")

from difflib import get_close_matches
# Command suggestions config (add after imports)
COMMAND_SUGGESTIONS = {
    # /prices variants
    'price': '/prices',
    'prices': '/prices',
    'prize': '/prices',
    'pice': '/prices',
    'prc': '/prices',
    'tokenprice': '/prices',
    
    # /balance variants
    'balance': '/balance',
    'bal': '/balance',
    'blance': '/balance',
    'wallet': '/balance',
    'wallets': '/balance',
    'balanse': '/balance',
    
    # /whalealert variants
    'whale': '/whalealert',
    'whales': '/whalealert',
    'wale': '/whalealert',
    'whalealrt': '/whalealert',
    'bigtransfers': '/whalealert',
    'bigtx': '/whalealert',
    
    # /chart variants
    'chart': '/chart',
    'charts': '/chart',
    'chrt': '/chart',
    'pricechart': '/chart',
    'graph': '/chart',
    
    # /tokendetails variants
    'details': '/tokendetails',
    'tokeninfo': '/tokendetails',
    'tokendetail': '/tokendetails',
    'metadat': '/tokendetails',
    'tokenstats': '/tokendetails',
    
    # /topholders variants
    'holders': '/topholders',
    'richlist': '/topholders',
    'topwallets': '/topholders',
    'bigbags': '/topholders',
    'whalewallets': '/topholders',
    
    # /nft_analysis variants
    'nft': '/nft_analysis',
    'nfts': '/nft_analysis',
    'nftstats': '/nft_analysis',
    'nftanalysis': '/nft_analysis',
    'collection': '/nft_analysis',
    'collections': '/nft_analysis',
    'nftdetails': '/nft_analysis',

    # tutorial variants
    'tutorial': '/tutorial',
    'tutorials': '/tutorial',
    'guide': '/tutorial',
    'learn': '/tutorial',
    'helpme': '/tutorial',
    
    # General
    'start': '/start',
    'help': '/start',
    'commands': '/start',

    'pyth': '/pyth',
    'pythe': '/pyth',
    'oracle': '/pyth',
    'pricefeed': '/pyth',
    'oracledata': '/pyth',
    
    # more variants for other commands
    'nftanalysis': '/nft_analysis',
    'nftstats': '/nft_analysis',
    'nftholders': '/nft_analysis',
    'collection': '/nft_analysis',
    
    'holders': '/topholders',
    'richlist': '/topholders',
    'whales': '/topholders',
    
    'charting': '/chart',
    'graph': '/chart',
    'pricechart': '/chart',
}

async def handle_typos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Smart typo handler with flow awareness"""
    uid = update.effective_user.id
    
    # Ignore messages during active flows
    if uid in USER_STATE:
        return
    
    # Ignore messages with buttons
    if update.message.reply_markup:
        return
    user_text = update.message.text.lower().strip()
    
    # Check if we're in a flow state
    uid = update.effective_user.id
    if uid in USER_STATE:
        return  # Don't interfere with active flows
    
    # Remove accidental command slashes
    clean_text = user_text.lstrip('/')
    
    # Find best matches with higher cutoff
    matches = get_close_matches(clean_text, COMMAND_SUGGESTIONS.keys(), n=2, cutoff=0.7)
    
    if matches:
        suggestions = [COMMAND_SUGGESTIONS[m] for m in matches[:2]]
        unique_suggestions = list(dict.fromkeys(suggestions))  # Preserve order
        
        if len(unique_suggestions) > 1:
            suggestion_text = " or ".join(unique_suggestions)
        else:
            suggestion_text = unique_suggestions[0]
        
        await update.message.reply_text(
            f"🔍 Did you mean {suggestion_text}?\n"
            "Try one of these commands:\n"
            "• /prices - Token prices\n"
            "• /balance - Wallet balances\n"
            "• /chart - Price charts\n"
            "• /topholders - Top token holders\n\n"
            "📋 Full list: /start",
            parse_mode="Markdown"
        )
    else:
        caption = (
            "🤖Try these:\n"
            "• /start - Show main menu\n"
            "• /tutorial - Beginner's guide\n"
            "• Type /commands for full list"
        )
        keyboard = [InlineKeyboardButton("ALPHAVYBE", url="https://vybe.fyi/")]
        await update.message.reply_text(
            caption=caption,
            reply_markup = InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


async def tutorial_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Starts the interactive tutorial with Vybevigil's analytic edge
    """
    context.user_data["tutorial_step"] = 1
    text = (
        "🔮 **VybeVigil Analytics bot Tutorial** 🔮\n\n"
        "Step 1: **Core Commands**\n"
        "• `/prices` - Track token values\n"
        "• `/balance <wallet>` - Check SOL holdings\n"
        "• `/whalealert` - Spot big moves\n\n"
        "Hit **Next** to dive deeper into analytics"
    )
    keyboard = [[InlineKeyboardButton("Next ➡️", callback_data="tutorial_next")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def tutorial_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles tutorial navigation with chain analysis flair
    """
    query = update.callback_query
    await query.answer()

    step = context.user_data.get("tutorial_step", 1)
    
    # Navigation logic
    if query.data == "tutorial_next":
        step += 1
    elif query.data == "tutorial_back":
        step = max(1, step - 1)
    elif query.data == "tutorial_restart":
        step = 1
        
    context.user_data["tutorial_step"] = step

    # Step content
    if step == 1:
        text = (
            "🔮 **Step 1: Core Commands** 🔮\n\n"
            "• `/prices` - Track token values\n"
            "• `/balance <wallet>` - Check SOL holdings\n"
            "• `/whalealert` - Spot big moves\n\n"
            "Pro Tip: Add number parameters like `/whalealert 5000 5`"
        )
    elif step == 2:
        text = (
            "📊 **Step 2: Deep Analysis** 📊\n\n"
            "• `/tokendetails <MINT>` - Full token metrics\n"
            "• `/topholders <MINT>` - Whale wallets\n"
            "• `/chart <MINT>` - Price history\n\n"
            "Try: `/tokendetails EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`"
        )
    elif step == 3:
        text = (
            "🛠️ **Step 3: Advanced Tools** 🛠️\n\n"
            "• `/nft_analysis` - Collection stats\n"
            "• Web Dashboard - Full analytics\n"
            "• Custom alerts - Coming soon!\n\n"
            "Pro Tip: Use our web interface for deep dives!"
        )
    else:
        text = (
            "🎉 **Tutorial Complete!** 🎉\n\n"
            "You're now ready to:\n"
            "• Track whale movements 🐋\n"
            "• Analyze token distributions 📊\n"
            "• Monitor NFT collections 🖼️\n\n"
            "Type /tutorial again for a refresher!"
        )
        keyboard = [[InlineKeyboardButton("🔄 Restart", callback_data="tutorial_restart")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="Markdown")
        return

    # Dynamic buttons
    buttons = []
    if step > 1:
        buttons.append(InlineKeyboardButton("⬅️ Back", callback_data="tutorial_back"))
    if step < 3:
        buttons.append(InlineKeyboardButton("Next ➡️", callback_data="tutorial_next"))
    
    reply_markup = InlineKeyboardMarkup([buttons])
    await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="Markdown")  
# async def token_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Handle /tokendetails command"""
#     if not context.args:
#         await update.message.reply_text("⚠️ Please provide a token mint address\nExample: /tokenDetails EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
#         return
#     token_mint = context.args[0]
#     token_info = await slashutils.get_token_details(token_mint)
#     await update.message.reply_text(token_info, parse_mode="Markdown")
from playwright.async_api import async_playwright
import asyncio

async def token_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /tokendetails command"""
    if not context.args:
        await update.message.reply_text(
            "⚠️ Please provide a token mint address\nExample: /tokenDetails EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        )
        return

    token_mint = context.args[0]
    url = f"https://vybe.fyi/tokens/{token_mint}"
    screenshot_path = f"screenshot_{token_mint}.png"

    # Send a "Loading" message to the user
    loading_message = await update.message.reply_text("⏳ Loading chart with token details...")

    # Get token details (assuming slashutils.get_token_details works as before)
    token_info = await slashutils.get_token_details(token_mint)

    # Use Playwright to take a screenshot
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            # Navigate to the page with a timeout
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for the cookie popup to appear
            # try:
            #     await page.wait_for_selector('button[title="ACCEPT ALL"]', state="visible", timeout=10000)
            #     # Click the "ACCEPT ALL" button to dismiss the cookie popup
            #     await page.click('button[title="ACCEPT ALL"]')
            #     # Wait for the popup to disappear
            #     await page.wait_for_selector('button[title="ACCEPT ALL"]', state="detached", timeout=5000)
            # except Exception as e:
            #     print(f"No cookie popup found or error handling popup: {e}")

            # Wait for the chart canvas to be visible
            chart_found = False
            try:
                # Use the generic selector for the canvas inside chart-gui-wrapper
                await page.wait_for_selector('div.chart-gui-wrapper canvas', state="visible", timeout=15000)
                chart_found = True

                # Add a longer delay to ensure chart data is loaded and rendered
                # await asyncio.sleep(5)  # Increased to 5 seconds for chart rendering

                # Scroll to the chart area to ensure it’s in view and fully rendered
                await page.evaluate("document.querySelector('div.chart-gui-wrapper canvas').scrollIntoView()")
                # await asyncio.sleep(2)  # Increased delay after scrolling to 2 seconds

                # Optional: Check if the chart has a loading spinner and wait for it to disappear
                try:
                    await page.wait_for_selector('div.chart-gui-wrapper .loading-spinner', state="detached", timeout=10000)
                except Exception:
                    pass  # No spinner or already gone
            except Exception as e:
                print(f"Chart not found or failed to load: {e}")

            # Take screenshot
            await page.screenshot(path=screenshot_path, full_page=True)

            # Reply with both screenshot and token info, with a note if chart is missing
            caption = token_info
            keyboard = [InlineKeyboardButton("Track live on ALPHAVYBE", url=f"https://vybe.fyi/tokens/{token_mint}")]
            if not chart_found:
                caption += "⚠️ Note: Chart may be missing or failed to load in the screenshot."
            await update.message.reply_photo(
                photo=open(screenshot_path, "rb"),
                caption=caption,
                reply_markup=InlineKeyboardMarkup([keyboard]),
                parse_mode="Markdown"
            )

            # Optionally delete the "Loading" message after the main message is sent
            await loading_message.delete()

        except Exception as e:
            # Delete the "Loading" message if an error occurs
            await loading_message.delete()
            await update.message.reply_text(
                f"⚠️ Error generating screenshot: {str(e)}\n\nToken Info:\n{token_info}",
                parse_mode="Markdown"
            )
        finally:
            await browser.close()

    # Clean up screenshot file
    if os.path.exists(screenshot_path):
        os.remove(screenshot_path)

async def get_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet_address = context.args[0] if context.args else None
    if not wallet_address:
        await update.message.reply_text("Please provide a wallet address")
        return
    
    balance = await slashutils.get_wallet_balance(wallet_address)
    await update.message.reply_text(f"💰 Wallet Balance:\n{balance} SOL", parse_mode="Markdown")

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
        # Ensure context.args is not None before accessing elements.
        if context.args is None:
            threshold = 5000
            alert_count = 5
        else:
            threshold = float(context.args[0]) if len(context.args) > 0 else 1000
            alert_count = int(context.args[1]) if len(context.args) > 1 else 7

        # Fetch whale transfers asynchronously.
        alerts = await slashutils.detect_whale_transfers(cap=threshold)
        alerts = alerts[:alert_count]

        if alerts:
            message = (
                f"🔔 **Top {len(alerts)} Whale Transfers** (≥ ${threshold:.0f}):\n\n"
                f"[Track Whales Live](https://alpha.vybenetwork.com/wallets/whales?order=totalSum&desc=true&preset=SOL+Whales)\n\n"
            )
            for i, transfer in enumerate(alerts, start=1):
                block_time = transfer.get('blockTime')
                if block_time:
                    readable_time = datetime.fromtimestamp(block_time).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    readable_time = 'N/A'
                message += (
                    f"**{i}.** \n • Signature: 🔑 `{transfer.get('signature', 'N/A')}`\n"
                    f"    • 📤 Sender: `{transfer.get('senderAddress', 'N/A')}`\n"
                    f"    • 📥 Receiver: `{transfer.get('receiverAddress', 'N/A')}`\n"
                    f"    • 💰 Amount: {transfer.get('calculatedAmount', 'N/A')} raw\n"
                    f"    • 💵 Value: ${transfer.get('valueUsd', 'N/A'):.2f}\n"
                    f"    • ⏰ {readable_time} UTC\n\n"
                )
        else:
            message = "No whale transfers found exceeding the threshold."

        # If this update is a callback query, answer it to remove the spinner.
        if update.callback_query:
            await update.callback_query.answer()

        # Use effective_message to cover both message and callback query scenarios.
        target_message = update.effective_message
        if target_message is None:
            logging.error("No valid message found in update!")
            return

        # Telegram has a character limit per message; send in chunks if needed.
        for chunk in slashutils.chunk_message(message):
            await target_message.reply_text(chunk, parse_mode="Markdown")

    except ValueError:
        # On error, notify the user using the effective message.
        target_message = update.effective_message
        if target_message:
            await target_message.reply_text("❌ Invalid input. Usage: /whalealert <threshold> [alert count]")

async def send_chunks(update: Update, text: str, chunk_size: int = 4096):
    """Send text in Telegram message chunks if it's too long."""
    for chunk in slashutils.chunk_message(text, chunk_size):
        await update.message.reply_text(chunk,parse_mode="Markdown")

async def check_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /prices command.

    Usage:
      /prices                -> Displays 10 tokens (default)
      /prices 15             -> Displays 15 tokens
      /prices <token_mint>   -> Displays details for the specified token
    """
    # If no arguments, show default 10 tokens.
    if not context.args:
        price_info = await slashutils.get_token_price(count=10)
        await send_chunks(update, price_info)
        return

    # If the first argument is a number, treat it as the desired count.
    try:
        count = int(context.args[0])
        price_info = await slashutils.get_token_price(count=count)
        await send_chunks(update, price_info)
    except ValueError:
        # Otherwise, assume the argument is a token mint address.
        token_mint = context.args[0]
        price_info = await slashutils.get_token_price(token_mint=token_mint)
        await send_chunks(update, price_info)

async def top_token_holders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 1:
            await update.message.reply_text("❌ Usage: /topholders <mintAddress> [count]")
            return

        mint_address = context.args[0]
        count = int(context.args[1]) if len(context.args) > 1 else 10

        holders = await slashutils.get_top_token_holders(mint_address, count)

        if not holders:
            await update.message.reply_text("😕 No data found for this token.", parse_mode="Markdown")
            return

        # message = f"👑 *Top {count} Holders of Token:* `{mint_address}`\n\n"
        token_symbol = holders[0].get("tokenSymbol", "N/A")
        message = (
            f"👑 *Top {count} Holders of Token:* `{mint_address}` — *{token_symbol}*\n"
            f"🔔 [see more insights on Alphavybe](https://alpha.vybenetwork.com/)\n\n"
        )


        for holder in holders:
            message += (
                f"🏅 Rank: {holder.get('rank', 'N/A')}\n"
                f"🧾 Name: {holder.get('ownerName') or 'N/A'}\n"
                f"📦 Address: `{holder.get('ownerAddress')}`\n"
                f"💰 Balance: {holder.get('balance', 'N/A')}\n"
                f"💵 USD Value: ${float(holder.get('valueUsd', 0)):.2f}\n"
                f"📈 % Supply Held: {holder.get('percentageOfSupplyHeld', 0):.4f}%\n\n"
                # f"🔔 [see more insights](https://alpha.vybenetwork.com/)\n\n\n\n"

            )

        for chunk in slashutils.chunk_message(message):
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
        ohlcv_data = await slashutils.fetch_ohlcv_data(mint_address, resolution, time_start, time_end)
        if not ohlcv_data:
            await update.message.reply_text("No data available for the provided mint address.")
            return

        chart_image = await slashutils.generate_price_chart(ohlcv_data)
        token_name = await slashutils.get_token_name_for_chart(mint_address)
        await update.message.reply_text(f"{token_name}📈 Price Chart:", parse_mode="Markdown")
        await update.message.reply_photo(photo=chart_image)
        # [see more insights](https://alpha.vybenetwork.com/)
        await update.message.reply_text(f"🔔 See more insights: https://alpha.vybenetwork.com/tokens/{mint_address})\n", parse_mode="Markdown")
    except aiohttp.ClientResponseError as e:
        await update.message.reply_text(f"Failed to fetch data: {e}")
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")
    
# NFT Collection Statistics
# NFT ANALYSIS
async def nft_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a collection address")
        return
    
    collection_address = context.args[0]
    analysis = await slashutils.get_nft_analysis(collection_address)
    
    if not analysis['text_report']:
        await update.message.reply_text("😕Could not retrieve NFT data for this collection")
        return
    
    await update.message.reply_text(
        analysis['text_report'], 
        parse_mode="Markdown"
    )
    
    if analysis['chart_image']:
        await update.message.reply_photo(photo=analysis['chart_image'])
