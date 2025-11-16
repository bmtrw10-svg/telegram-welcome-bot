import os
import threading
import asyncio
import re
from collections import defaultdict
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, CommandHandler, filters
from telegram.error import BadRequest, Forbidden
from http.server import HTTPServer, BaseHTTPRequestHandler

# === TOKEN ===
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("Set 'TOKEN' in Render Environment Variables!")

# === STATS ===
join_count = 0
spam_count = 0
last_spammer = {}

# === HTTP DASHBOARD ===
class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(f"""
        <h1>🤖 Pro Welcome Bot v3 - LIVE</h1>
        <p>Joins: {join_count} | Spammers muted: {spam_count}</p>
        <p>Status: <span style="color:green">RUNNING</span></p>
        """.encode())
    def log_message(self, *args): pass

def run_http_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("", port), DashboardHandler)
    print(f"Dashboard: https://your-service.onrender.com")
    server.serve_forever()

# === WELCOME (DM + GROUP FALLBACK + TEMP PIN) ===
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global join_count
    if not update.message or not update.message.new_chat_members:
        return
    join_count += 1
    chat = update.message.chat
    for member in update.message.new_chat_members:
        username = member.username or member.first_name
        user_id = member.id

        # 1. Try DM
        dm_success = False
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    f"👋 Welcome @{username}!\n\n"
                    "📜 **Group Rules**\n"
                    "1. No spam or ads\n"
                    "2. Be kind and respectful\n"
                    "3. English only\n\n"
                    "Enjoy your stay! 🚀"
                )
            )
            dm_success = True
        except (Forbidden, BadRequest):
            pass  # DM closed or blocked

        # 2. If DM fails → send in group + temp pin 30 sec
        if not dm_success:
            msg = await update.message.reply_text(
                f"👋 Welcome @{username}!\n\n"
                "📜 **Group Rules**\n"
                "1. No spam or ads\n"
                "2. Be kind and respectful\n"
                "3. English only\n\n"
                "*(DM closed — shown here for 30 sec)*"
            )
            # Pin
            try:
                await context.bot.pin_chat_message(chat_id=chat.id, message_id=msg.message_id, disable_notification=True)
            except: pass

            # Delete after 30 sec
            await asyncio.sleep(30)
            try:
                await msg.delete()
                await context.bot.unpin_chat_message(chat_id=chat.id, message_id=msg.message_id)
            except: pass

# === /stats ===
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📊 **Bot Stats**\n"
        f"Total joins: {join_count}\n"
        f"Spammers muted: {spam_count}"
    )

# === ANTI-SPAM (AUTO-MUTE) ===
async def antispam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global spam_count
    msg = update.message
    if not msg or not msg.text or msg.from_user.is_bot:
        return
    user_id = msg.from_user.id
    text = msg.text

    links = re.findall(r'http[s]?://', text)
    if len(links) >= 2:
        if user_id in last_spammer and (asyncio.get_event_loop().time() - last_spammer[user_id] < 60):
            try:
                await msg.delete()
                await context.bot.restrict_chat_member(
                    chat_id=msg.chat.id,
                    user_id=user_id,
                    permissions={'can_send_messages': False}
                )
                spam_count += 1
                await msg.reply_text(f"🔇 @{msg.from_user.username} muted for spam!")
            except: pass
        else:
            last_spammer[user_id] = asyncio.get_event_loop().time()

# === MAIN ===
def main():
    threading.Thread(target=run_http_server, daemon=True).start()

    print("Pro Welcome Bot v3 starting...")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, antispam))

    app.run_polling()

if __name__ == "__main__":
    main()
