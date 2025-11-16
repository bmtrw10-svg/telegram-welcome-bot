import os
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

# === GET TOKEN FROM RENDER (NEVER HARDCODE) ===
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("ERROR: Set 'TOKEN' in Render Environment Variables!")

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.new_chat_members:
        for member in update.message.new_chat_members:
            username = member.username or member.first_name
            await update.message.reply_text(
                f"Welcome @{username}!\n\n"
                "Group Rules\n"
                "1. No spam or ads\n"
                "2. Be kind and respectful\n"
                "3. English only"
            )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
