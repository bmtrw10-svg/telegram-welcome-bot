import os
import threading
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# === GET TOKEN FROM RENDER ===
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("ERROR: Set 'TOKEN' in Render Environment Variables!")

# === DUMMY HTTP SERVER (FOR RENDER HEALTH CHECKS) ===
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")  # Render pings this → "alive!"

    def log_message(self, format, *args):
        pass  # Silent logs

# === WELCOME FUNCTION ===
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

# === START BOT POLLING ===
def start_bot():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    print("Bot is running...")
    app.run_polling()

# === MAIN ===
def main():
    # Get Render's port (or default 10000)
    port = int(os.getenv("PORT", 10000))
    
    # Start HTTP server in main thread (binds to port for Render)
    server = HTTPServer(("", port), HealthHandler)
    print(f"HTTP server on port {port} for Render health checks")
    
    # Start bot polling in background thread
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Run HTTP server forever
    server.serve_forever()

if __name__ == "__main__":
    main()
