# handlers/state.py
from telegram import InlineKeyboardButton

USER_STATE = {}
CANCEL_BUTTON = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel_operation")]]