import requests
from config import Config
import logging

logger = logging.getLogger(__name__)

class VybeAPI:
    def __init__(self):
        self.base_url = "https://api.vybenetwork.com/v1"
        self.headers = {"Authorization": f"Bearer {Config.VYBE_API_KEY}"}

    def _get(self, endpoint, params=None):
        try:
            response = requests.get(f"{self.base_url}/{endpoint}", 
                                  headers=self.headers, 
                                  params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Vybe API Error: {str(e)}")
            return None

    # Account Endpoints
    def get_token_balance(self, owner_address):
        return self._get(f"account/token-balance/{owner_address}")
    
    def get_nft_balance(self, owner_address):
        return self._get(f"account/nft-balance/{owner_address}")
    
    def get_known_accounts(self):
        return self._get("account/known-accounts")
    
    # Token Endpoints
    def get_token_details(self, mint_address):
        return self._get(f"token/{mint_address}")
    
    def get_top_holders(self, mint_address):
        return self._get(f"token/{mint_address}/top-holders")
    
    # Price Endpoints
    def get_token_price(self, mint_address):
        return self._get(f"price/{mint_address}/token-ohlcv")
    
    # Program Endpoints
    def get_program_details(self, program_id):
        return self._get(f"program/{program_id}")