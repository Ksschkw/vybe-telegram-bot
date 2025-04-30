from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
VYBE_API_KEY    = os.getenv("VYBE_API_KEY")
VYBE_BASE_URL   = "https://api.vybenetwork.xyz"