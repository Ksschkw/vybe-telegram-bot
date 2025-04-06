import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
VYBE_API_KEY = os.getenv("VYBE_API_KEY")
VYBE_BASE_URL = "https://api.vybenetwork.xyz"

async def get_wallet_balance(wallet_address):
    url = f"{VYBE_BASE_URL}/account/token-balance-ts/{wallet_address}"
    headers = {"X-API-KEY": VYBE_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return f"Wallet: {wallet_address[:6]}...{wallet_address[-4:]}\n" \
               f"Balance: {data.get('balance', 0):.2f} SOL\n" \
               f"Tokens: {data.get('token_count', 0)}"
    except Exception as e:
        return f"❌ Error fetching balance: {str(e)}"
    
#              Check for whale transfers
async def detect_whale_transfers(min_amount: float = 1000):
    """Detect large token transfers using Vybe's transfers endpoint"""
    url = f"{VYBE_BASE_URL}/token/transfers"
    headers = {"X-API-KEY": VYBE_API_KEY}
    
    params = {
        "sort": "-amount",
        "limit": 5,
        "currency": "SOL",
        "amount_gt": min_amount * 1e9  # Convert SOL to lamports
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        whale_alerts = []
        for transfer in data.get('data', [])[:3]:  # Top 3 largest
            alert = (
                f"🐳 WHALE ALERT! 🚨\n"
                f"Amount: {transfer['amount']/1e9:.2f} SOL\n"
                f"From: {transfer['from'][:6]}...{transfer['from'][-4:]}\n"
                f"To: {transfer['to'][:6]}...{transfer['to'][-4:]}\n"
                f"Token: {transfer['mint']}\n"
                f"TX: https://explorer.solana.com/tx/{transfer['signature']}"
            )
            whale_alerts.append(alert)
            
        return "\n\n".join(whale_alerts) if whale_alerts else "No recent whale activity"
        
    except Exception as e:
        return f"⚠️ Whale detection failed: {str(e)}"
    
async def get_token_price(token_mint: str):
    """Get token price with robust error checking"""
    url = f"{VYBE_BASE_URL}/v1/tokens/{token_mint}"
    headers = {"X-API-KEY": VYBE_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check HTTP errors
        data = response.json()
        
        # Validate response structure
        if not all(key in data for key in ['symbol', 'name', 'price']):
            return "⚠️ Invalid token data format from API"
            
        return (
            f"📊 {data['symbol']} ({data['name']})\n"
            f"Price: ${data['price']:.4f}\n"
            f"24h Change: {data.get('change_24h', 0):.2f}%\n"
            f"Volume: ${data.get('volume_24h', 0):,.2f}\n"
            f"Market Cap: ${data.get('market_cap', 0):,.2f}"
        )
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return "❌ Token not found - check mint address"
        return f"⚠️ API Error: {e.response.status_code}"
    except KeyError as e:
        return f"🔧 Missing data field: {str(e)}"
    except Exception as e:
        return f"🚨 Unexpected error: {str(e)}"