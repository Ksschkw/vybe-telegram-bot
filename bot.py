from telegram.ext import Application, CommandHandler
from config import TELEGRAM_TOKEN
from slashmain import *

import handlers.start       as start_h
import handlers.accounts    as acct_h
import handlers.prices      as prices_h
import handlers.chart       as chart_h
import handlers.holders     as holders_h
import handlers.nft_analysis as nft_h
import handlers.pyth        as pyth_h
import handlers.tutorial    as tut_h
import handlers.whale_alert as whale_h

app = Application.builder().token(TELEGRAM_TOKEN).build()

# /start menu
app.add_handler(CommandHandler("start", start_h.start))
for h in start_h.menu_handlers:
    app.add_handler(h)

# Flows
for h in acct_h.handlers:    app.add_handler(h)
for h in prices_h.handlers:  app.add_handler(h)
for h in chart_h.handlers:   app.add_handler(h)
for h in holders_h.handlers: app.add_handler(h)
for h in nft_h.handlers:     app.add_handler(h)
for h in pyth_h.handlers:    app.add_handler(h)
for h in tut_h.handlers:     app.add_handler(h)


#Handle Typos
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_typos))

# Whale Alert
app.add_handler(CallbackQueryHandler(whale_h.start_whale, pattern="^menu_whale$"))
for h in whale_h.handlers:
    app.add_handler(h)

#Slash command handlers
app.add_handler(CommandHandler("balance", get_balance))
app.add_handler(CommandHandler("whalealert", whale_alert))
app.add_handler(CommandHandler("prices", check_prices))
app.add_handler(CommandHandler("tokenDetails", token_details))
app.add_handler(CommandHandler("topholders", top_token_holders))
app.add_handler(CommandHandler("chart", chart))
app.add_handler(CommandHandler("nft_analysis", nft_analysis))
app.add_handler(CommandHandler("tutorial", tutorial_start))
app.add_handler(CallbackQueryHandler(tutorial_callback, pattern="^tutorial_"))

# Start polling
app.run_polling()
