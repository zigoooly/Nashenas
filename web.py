from flask import Flask, request
from telegram import Update
import asyncio
from bot import application

app = Flask(__name__)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# 🔹 فقط یک بار در شروع
loop.run_until_complete(application.initialize())
loop.run_until_complete(application.start())

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)

    loop.create_task(application.process_update(update))
    return "ok"

@app.route("/")
def home():
    return "Bot is running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
