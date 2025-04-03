import requests
from config import Config

class VybeAPI:
    def __init__(self):
        self.base_url = "https://api.vybenetwork.com/v1"
        self.headers = {"Authorization": f"Bearer {Config.VYBE_API_KEY}"}

    def _get(self, endpoint, params=None):
        return requests.get(f"{self.base_url}/{endpoint}", headers=self.headers, params=params).json()

    def get_wallet_balance(self, address):
        return self._get(f"wallets/{address}/balance")
    
    def get_portfolio(self, address):
        return self._get(f"wallets/{address}/portfolio")
    
    def get_token_metrics(self, contract):
        return self._get(f"tokens/{contract}/metrics")
    
    def get_whale_transactions(self, min_value):
        return self._get("transactions/whales", {"min_value": min_value})
    
    def get_nft_holdings(self, address):
        return self._get(f"wallets/{address}/nfts")
    
    def get_gas_prices(self):
        return self._get("network/gas")
    
    def get_dex_trades(self, token):
        return self._get(f"dex/{token}/trades")