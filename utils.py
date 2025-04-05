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