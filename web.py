from flask import Flask
import threading
from bot import build_app

app = Flask(__name__)
telegram_app = build_app()

def run_bot():
    telegram_app.run_polling()

@app.route("/")
def home():
    return "Bot is running"

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=8080)
