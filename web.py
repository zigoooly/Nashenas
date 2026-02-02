from flask import Flask
import asyncio
from bot import build_app

app = Flask(__name__)

telegram_app = build_app()

@app.before_first_request
def start_bot():
    asyncio.get_event_loop().create_task(telegram_app.initialize())
    asyncio.get_event_loop().create_task(telegram_app.start())
    asyncio.get_event_loop().create_task(telegram_app.bot.initialize())
    asyncio.get_event_loop().create_task(telegram_app.updater.start_polling())

@app.route("/")
def home():
    return "Bot is running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
