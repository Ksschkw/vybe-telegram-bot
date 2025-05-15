from telegram.ext import ApplicationBuilder
from bot import setup_bot

if __name__ == "__main__":
    application = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()
    setup_bot(application)
    application.run_polling()