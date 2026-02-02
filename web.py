from flask import Flask
import asyncio
from bot import build_app

app = Flask(__name__)
telegram_app = build_app()

async def start_bot():
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.initialize()
    await telegram_app.updater.start_polling()

@app.route("/")
def home():
    return "Bot is running"

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(start_bot())
    app.run(host="0.0.0.0", port=8080)
