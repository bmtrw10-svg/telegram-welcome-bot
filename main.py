import os
import threading
import asyncio
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from http.server import HTTPServer, BaseHTTPRequestHandler

# === GET TOKEN ===
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("ERROR: Set 'TOKEN' in Render Environment Variables!")

# === DUMMY HTTP SERVER ===
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args): pass

# === WELCOME ===
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

# === HTTP SERVER IN BACKGROUND ===
def run_http_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("", port), HealthHandler)
    print(f"HTTP server running on port {port}")
    server.serve_forever()

# === MAIN: RUN POLLING IN MAIN THREAD ===
def main():
    # Start HTTP server in background
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    # Build and run bot in main thread (has event loop)
    print("Starting Telegram bot polling...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.run_polling()

if __name__ == "__main__":
    main()
