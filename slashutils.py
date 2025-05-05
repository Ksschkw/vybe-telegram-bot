import matplotlib
matplotlib.use('Agg')
from datetime import datetime, UTC
import requests
import os
from dotenv import load_dotenv
import json
import aiohttp
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
# from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Load environment variables
load_dotenv()
VYBE_API_KEY = os.getenv("VYBE_API_KEY")
VYBE_BASE_URL = "https://api.vybenetwork.xyz"
VYBE_API_URL = "https://api.vybenetwork.xyz/price"

async def get_wallet_balance(wallet_address):
    """Get and format wallet balance in user-friendly way"""
    url = f"{VYBE_BASE_URL}/account/token-balance/{wallet_address}"
    headers = {
        "accept": "application/json",
        "X-API-KEY": VYBE_API_KEY
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Format timestamp
        ts = data.get('date')
        formatted_date = datetime.fromtimestamp(ts/1000).strftime('%Y-%m-%d %H:%M:%S') if ts else "Unknown"

        # Format balances
        sol_balance = float(data.get('stakedSolBalance', 0))
        token_count = int(data.get('totalTokenCount', 0))

        return (
            f"💼  Wallet Overview  💼\n\n"
            f"🔑 Address: `{wallet_address[:6]}...{wallet_address[-4:]}`\n"
            f"🕒 Last Updated: {formatted_date}\n\n"
            f"💰  SOL Balance : {sol_balance:.4f} SOL\n"
            f"📊  Total Tokens : {token_count:,}\n"
            f"💵  Total Value : ${float(data.get('totalTokenValueUsd', 0)):.2f}\n\n"
            f"🔒  Staked SOL : {float(data.get('activeStakedSolBalance', 0)):.4f} SOL"
        )

    except requests.exceptions.HTTPError as e:
        return f"❌ API Error: {e.response.status_code} - Check wallet address"
    except json.JSONDecodeError:
        return "⚠️ Failed to parse balance data"
    except Exception as e:
        return f"🚨 Error: {str(e)}"

# Helper function to split long messages
def chunk_message(text, chunk_size=4096):
    """Breaks text into chunks no larger than chunk_size characters."""
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

# Asynchronous version of detect_whale_transfers using aiohttp
async def detect_whale_transfers(cap=10.0):
    """
    Asynchronously fetch token transfers from the Vybe API and filter out transfers
    where the USD value is greater than or equal to the provided cap.

    Parameters:
        api_key (str): Your API key for authentication.
        cap (float): The USD value threshold for determining a whale transfer.
    
    Returns:
        list of dict: Each dict contains details about a whale transfer.
    """
    url = "https://api.vybenetwork.xyz/token/transfers"
    headers = {
        "accept": "application/json",
        "X-API-KEY": VYBE_API_KEY
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                print(f"Error fetching transfers, status code: {response.status}")
                return []
            data = await response.json()
            
    transfers = data.get("transfers", [])
    whale_transfers = []
    
    for transfer in transfers:
        try:
            value_usd = float(transfer.get("valueUsd", "0"))
        except (ValueError, TypeError):
            continue

        if value_usd >= cap:
            whale_transfers.append({
                "signature": transfer.get("signature"),
                "senderAddress": transfer.get("senderAddress"),
                "receiverAddress": transfer.get("receiverAddress"),
                "amount": transfer.get("amount"),
                "calculatedAmount": transfer.get("calculatedAmount"),
                "valueUsd": value_usd,
                "blockTime": transfer.get("blockTime"),
            })
    return whale_transfers

async def get_token_price(
    token_mint: str = None,
    count: int = 10,
    sort_by: str = None,
    page: int = 1,
    filter_zero_price: bool = True,
) -> str:
    """
    Asynchronously retrieves token price data from the Vybe API.
    
    If a token mint address is provided, returns details for that token.
    Otherwise, it returns a formatted string containing details for the first
    `count` tokens (after filtering).

    Parameters:
      token_mint (str, optional): Specific token mint address to filter on.
      count (int, optional): Number of tokens to return (default 10).
      sort_by (str, optional): Field name to sort by. One of:
           mintAddress, currentSupply, marketCap, name, price, symbol.
      page (int, optional): Page number for paginated results.
      filter_zero_price (bool, optional): If True, tokens with price 0 are excluded.
      api_key (str): Your Vybe API key.
    
    Returns:
      str: A formatted string of token details.
    """
    url = "https://api.vybenetwork.xyz/tokens"
    headers = {
        "accept": "application/json",
        "X-API-KEY": VYBE_API_KEY
    }
    params = {"page": page}
    if sort_by:
        allowed_fields = {"mintAddress", "currentSupply", "marketCap", "name", "price", "symbol"}
        if sort_by in allowed_fields:
            params["sort"] = sort_by
        else:
            return f"Invalid sort field '{sort_by}'. Allowed fields are: {', '.join(allowed_fields)}."

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    return f"Error: Received status code {response.status} from Vybe API."
                data = await response.json()
    except Exception as e:
        return f"Error fetching token data: {e}"

    tokens = data.get("data", [])
    if filter_zero_price:
        tokens = [token for token in tokens if token.get("price", 0) != 0]

    # If filtering by token mint address, only return matching token(s)
    if token_mint:
        tokens = [token for token in tokens if token.get("mintAddress") == token_mint]
        if not tokens:
            return f"No token found with the mint address: {token_mint}"
    else:
        tokens = tokens[:count]  # Limit to the requested count

    if not tokens:
        return "No tokens available."

    # Format the token information into a message.
    # Example in the async get_token_price() function when formatting each token
    message = "💎 Token Price Data:\n\n"
    for token in tokens:
            # Convert blockTime to human-readable format
        block_time = token.get('updateTime')
        if block_time:
            updatetime = datetime.fromtimestamp(block_time).strftime('%Y-%m-%d %H:%M:%S')
        else:
            updatetime = 'N/A'
        message += (
            f"🏷️ Symbol: {token.get('symbol')}\n"
            f"💡 Name: {token.get('name')}\n"
            f"🏦 Mint Address: {token.get('mintAddress')}\n"
            f"💵 Price: {token.get('price')}\n"
            # f"⏳ Price 1D: {token.get('price1d')}\n"
            # f"📅 Price 7D: {token.get('price7d')}\n"
            f"🔢 Current Supply: {token.get('currentSupply')}\n"
            f"💼 Market Cap: {token.get('marketCap')}\n"
            f"⏰ Update Time: {updatetime}\n"
            f"\n"
            f"🔔 [View Tokens live](https://alpha.vybenetwork.com/tokens)\n\n\n\n"

            f"\n"
            # f"🌐 Logo URL: {token.get('logoUrl')}\n\n"
        )

    
    # If showing a limited number of tokens because token_mint was not specified,
    # append a prompt to let users know they can request more.
    if not token_mint:
        message += f"Showing first {count} tokens. To see more, use /prices <number>"

    return message
    
async def get_token_details(mintAddress):
    """Get token details with formatted output"""
    url = f"{VYBE_BASE_URL}/token/{mintAddress}"
    headers = {"X-API-KEY": VYBE_API_KEY, "accept": "application/json"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Format timestamp
        update_time = data.get('updateTime')
        formatted_date = datetime.fromtimestamp(update_time).strftime('%Y-%m-%d %H:%M:%S') if update_time else "N/A"

        # Format large numbers
        current_supply = "{:,.2f}".format(data.get('currentSupply', 0))
        market_cap = "${:,.2f}".format(data.get('marketCap', 0)) if data.get('marketCap') else "N/A"

        return (
            f"🔍 {data.get('name', 'Unknown Token')} ({data.get('symbol', 'N/A')})\n\n"
            f"🆔 Mint Address: `{mintAddress[:6]}...{mintAddress[-4:]}`\n\n"
            f"📅 Last Updated: {formatted_date}\n\n"
            f"💰 Price: ${data.get('price', 0):.4f}\n\n"
            f"📈 Market Cap: {market_cap}\n\n"
            f"🔄 Current Supply: {current_supply}\n\n"
            f"🔢 Decimals: {data.get('decimal', 'N/A')}\n\n"
            f"✅ Verified: {'Yes' if data.get('verified') else 'No'}\n\n"
        )

    except Exception as e:
        return f"⚠️ Error fetching token details: {str(e)}"
    
async def get_top_token_holders(mint_address: str, count: int = 10):
    """
    Asynchronously fetches the top holders of a token from Vybe API.

    Args:
        mint_address (str): The token's mint address.
        count (int): Number of top holders to return. Defaults to 10.

    Returns:
        list of dict: Top token holders.
    """
    url = f"https://api.vybenetwork.xyz/token/{mint_address}/top-holders"
    headers = {
        "accept": "application/json",
        "X-API-KEY": VYBE_API_KEY
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                print(f"Error fetching top holders: {response.status}")
                return []
            data = await response.json()

    return data.get("data", [])[:count]

# TEESTING SOMETHING
async def get_token_name_for_chart(mintAddress):
    """Get token details with formatted output"""
    url = f"{VYBE_BASE_URL}/token/{mintAddress}"
    headers = {"X-API-KEY": VYBE_API_KEY, "accept": "application/json"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    return f" {data.get('name', 'Unknown Token')}"
# HISTORICAL CHART
async def fetch_ohlcv_data(mint_address, resolution, time_start, time_end):
    """
    Fetches OHLCV data from Vybe's API asynchronously.

    Parameters:
    - mint_address (str): The token's mint address.
    - resolution (str): Timeframe for each data point (e.g., '1h' for hourly).
    - time_start (int): Start time in Unix timestamp.
    - time_end (int): End time in Unix timestamp.

    Returns:
    - list: A list of OHLCV data points.
    """
    url = f"{VYBE_API_URL}/{mint_address}/token-ohlcv"
    headers = {
        "accept": "application/json",
        "X-API-KEY": VYBE_API_KEY
    }
    params = {
        "resolution": resolution,
        "timeStart": time_start,
        "timeEnd": time_end
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("data", [])
        
async def generate_price_chart(ohlcv_data):
    """
    Generates a price chart from OHLCV data asynchronously.

    Parameters:
    - ohlcv_data (list): A list of OHLCV data points.

    Returns:
    - BytesIO: In-memory image file of the generated chart.
    """
    # Convert timestamps to timezone-aware datetime objects
    dates = [datetime.fromtimestamp(item['time'], tz=UTC) for item in ohlcv_data]
    closes = [float(item['close']) for item in ohlcv_data]

    plt.figure(figsize=(10, 5))
    plt.plot(dates, closes, label='Close Price', color='blue')
    plt.xlabel('Date')
    plt.ylabel('Price (USD)')
    plt.title('Token Price Over Time')
    plt.legend()
    plt.grid(True)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gcf().autofmt_xdate()

    image_stream = BytesIO()
    plt.savefig(image_stream, format='png')
    plt.close()
    image_stream.seek(0)
    return image_stream

# NFT Collection Statistics
async def fetch_nft_collection_owners(collection_address: str) -> list:
    """Fetch NFT collection owners from Vybe API"""
    url = f"https://api.vybenetwork.xyz/nft/collection-owners/{collection_address}"
    headers = {
        "accept": "application/json",
        "X-API-KEY": VYBE_API_KEY
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('data', [])
            return []
def analyze_nft_owners(owners: list) -> dict:
    """Analyze NFT ownership distribution"""
    if not owners:
        return {}
    
    # Calculate ownership concentration
    ownership_count = {}
    for owner in owners:
        address = owner.get('address', 'unknown')
        ownership_count[address] = ownership_count.get(address, 0) + 1
    
    sorted_owners = sorted(ownership_count.items(), 
                         key=lambda x: x[1], 
                         reverse=True)
    
    return {
        "total_owners": len(ownership_count),
        "top_holder": sorted_owners[0] if sorted_owners else None,
        "average_per_holder": len(owners) / len(ownership_count) if ownership_count else 0,
        "concentration": dict(sorted_owners[:5])  # Top 5 holders
    }

async def get_nft_analysis(collection_address: str) -> dict:
    """Get NFT collection analysis using available data"""
    owners = await fetch_nft_collection_owners(collection_address)
    analysis = analyze_nft_owners(owners)
    
    return {
        'text_report': format_nft_report(collection_address, analysis),
        'chart_image': generate_ownership_chart(analysis)
    }

def format_nft_report(collection_address: str, analysis: dict) -> str:
    """Format NFT analysis report"""
    if not analysis:
        return "No ownership data available for this collection"
    
    concentration = "\n".join(
        [f"- {addr[:6]}...{addr[-4]}: {count} NFTs" 
         for addr, count in analysis.get('concentration', {}).items()]
    )
    # 📦 Total NFTs Tracked: {len(owners)}
    return f"""
🖼 *NFT Collection Analysis* 🖼

🔗 Collection Address: `{collection_address}`
👥 Unique Owners: {analysis.get('total_owners', 0)}
🏆 *Ownership Concentration*
{concentration}

📊 Average NFTs per Holder: {analysis.get('average_per_holder', 0):.1f}
🐳 Top Holder: {analysis.get('top_holder', ('', 0))[1]} NFTs
"""

def generate_ownership_chart(analysis: dict) -> BytesIO:
    """Generate ownership distribution chart"""
    if not analysis.get('concentration'):
        return None
    
    labels = [f"{addr[:3]}..{addr[-3]}" 
             for addr in analysis['concentration'].keys()]
    values = list(analysis['concentration'].values())
    
    plt.figure(figsize=(10, 5))
    plt.bar(labels, values, color='purple')
    plt.title("Top Holder NFT Distribution")
    plt.xlabel("Wallet Address")
    plt.ylabel("Number of NFTs")
    plt.xticks(rotation=45)
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf
