from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
from telegram import Update

USER_STATE = {}

async def tutorial_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    USER_STATE[update.effective_user.id] = {"flow": "tutorial", "step": 1}
    text = (
        "🔮 *VybeVigil Analytics bot Tutorial* 🔮\n\n"
        "Step 1: Core Commands\n"
        "• `/prices`  • `/balance <wallet>`  • `/whalealert`\n\n"
        "Hit Next ➡️"
    )
    kb = [[InlineKeyboardButton("Next ➡️", callback_data="tutorial_next")]]
    
    message = update.message or update.callback_query.message
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    if update.callback_query:
        await update.callback_query.answer()


async def tutorial_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    state = USER_STATE.get(uid, {"step": 1})
    step = state["step"]

    if q.data == "tutorial_next":
        step += 1
    elif q.data == "tutorial_back":
        step = max(1, step - 1)
    elif q.data == "tutorial_restart":
        step = 1

    USER_STATE[uid]["step"] = step

    if step == 1:
        text = (
            "🔮 *Step 1: Core Commands*\n"
            "• `/prices`\n• `/balance <wallet>`\n• `/whalealert`\n\nNext ➡️"
        )
        kb = [[InlineKeyboardButton("Next ➡️", callback_data="tutorial_next")]]
    elif step == 2:
        text = (
            "📊 *Step 2: Deep Analysis*\n"
            "• `/tokendetails <MINT>`\n"
            "• `/topholders <MINT>`\n"
            "• `/chart <MINT>`\n\n⬅️ Back • Next ➡️"
        )
        kb = [
            [InlineKeyboardButton("⬅️ Back", callback_data="tutorial_back"),
             InlineKeyboardButton("Next ➡️", callback_data="tutorial_next")]
        ]
    elif step == 3:
        text = (
            "🛠️ *Step 3: Advanced Tools*\n"
            "• `/nft_analysis`\n"
            "• Pyth OHLC\n"
            "• Custom alerts\n\n⬅️ Back"
        )
        kb = [[InlineKeyboardButton("⬅️ Back", callback_data="tutorial_back")]]
    else:
        text = "🎉 *Tutorial Complete!* 🎉\nType /tutorial to restart."
        kb = [[InlineKeyboardButton("🔄 Restart", callback_data="tutorial_restart")]]

    # Ensure keyboard is a list of lists
    if isinstance(kb[0], InlineKeyboardButton):
        kb = [kb]

    await q.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )


handlers = [
    CallbackQueryHandler(tutorial_callback, pattern="^tutorial_")
]
