from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from favorites_handlers.add_favorite_account import add_favorite_account
from favorites_handlers.favorite_accounts import favorite_accounts
from favorites_handlers.add_favorite_token import add_favorite_token
from favorites_handlers.favorite_tokens import favorite_tokens
from favorites_handlers.callbacks import (
    favorites_callback,
    account_balance_cb,
    token_details_cb,
    token_holders_cb,
    back_to_fav_accounts,
    back_to_fav_tokens
)

def setup_bot(app: Application):
    app.add_handler(CommandHandler("addfavoriteaccount", add_favorite_account))
    app.add_handler(CommandHandler("favoriteaccounts", favorite_accounts))
    app.add_handler(CommandHandler("addfavoritetoken", add_favorite_token))
    app.add_handler(CommandHandler("favoritetokens", favorite_tokens))
    app.add_handler(CallbackQueryHandler(favorites_callback, pattern="^fav_(acct|token):"))
    app.add_handler(CallbackQueryHandler(account_balance_cb, pattern="^acc_balance:"))
    app.add_handler(CallbackQueryHandler(token_details_cb, pattern="^tok_details:"))
    app.add_handler(CallbackQueryHandler(token_holders_cb, pattern="^tok_holders:"))
    app.add_handler(CallbackQueryHandler(back_to_fav_accounts, pattern="^back_fav_acct$"))
    app.add_handler(CallbackQueryHandler(back_to_fav_tokens, pattern="^back_fav_tok$"))