from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import TELEGRAM_TOKEN
from slashmain import (
    handle_typos,
    get_balance,
    whale_alert,
    check_prices,
    token_details,
    top_token_holders,
    chart,
    nft_analysis,
    tutorial_start,
    tutorial_callback
)

# Import handler modules
import handlers.start as start_h
import handlers.accounts as acct_h
import handlers.prices as prices_h
import handlers.chart as chart_h
import handlers.holders as holders_h
import handlers.nft_analysis as nft_h
import handlers.pyth as pyth_h
import handlers.tutorial as tut_h
import handlers.whale_alert as whale_h

app = Application.builder().token(TELEGRAM_TOKEN).build()

# ========================
# Handler Registration Order Matters!
# ========================

# 1. Command Handlers (Slash Commands)
app.add_handlers([
    CommandHandler("start", start_h.start),
    CommandHandler("balance", get_balance),
    CommandHandler("whalealert", whale_alert),
    CommandHandler("prices", check_prices),
    CommandHandler("tokendetails", token_details),  # Fixed naming consistency
    CommandHandler("topholders", top_token_holders),
    CommandHandler("chart", chart),
    CommandHandler("nft_analysis", nft_analysis),
    CommandHandler("tutorial", tutorial_start)
])

# 2. Callback Query Handlers (Menu System)
app.add_handlers([
    # Main menu handlers
    *start_h.menu_handlers,
    
    # Tutorial callback
    CallbackQueryHandler(tutorial_callback, pattern="^tutorial_"),
    
    # Whale Alert menu
    CallbackQueryHandler(whale_h.start_whale, pattern="^menu_whale$")
])

# 3. Flow Handlers (Message-based interactions)
all_flow_handlers = [
    *acct_h.handlers,
    *prices_h.handlers,
    *chart_h.handlers,
    *holders_h.handlers,
    *nft_h.handlers,
    *pyth_h.handlers,
    *tut_h.handlers,
    *whale_h.handlers
]

for handler in all_flow_handlers:
    app.add_handler(handler)

# 4. Typo Handler - MUST BE LAST!
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND & ~filters.Regex(r'^/'),
        handle_typos
    ),
    group=1  # Higher group number processes last
)

# ========================
# Start Polling
# ========================
if __name__ == "__main__":
    app.run_polling()