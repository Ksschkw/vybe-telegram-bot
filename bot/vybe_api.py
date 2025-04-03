import requests
import os
from dotenv import load_dotenv

load_dotenv('../config/.env')
VYBE_API_KEY = os.getenv("VYBE_API_KEY")

def get_token_price(token_address):
    url = f"https://api.vybenetwork.com/v1/price/{token_address}/token-ohlcv"
    headers = {"X-API-Key": VYBE_API_KEY}
    response = requests.get(url, headers=headers)
    return response.json()['close']

def get_token_data(token_address):
    url = f"https://api.vybenetwork.com/v1/token/{token_address}"
    headers = {"X-API-Key": VYBE_API_KEY}
    response = requests.get(url, headers=headers)
    return response.json()