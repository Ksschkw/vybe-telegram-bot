import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    VYBE_API_KEY = os.getenv("VYBE_API_KEY")
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    ALERT_THRESHOLD = 1000000  # Default whale alert threshold