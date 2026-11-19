from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram Ad Automation Bot is Running Live!"

def run_flask():
    # Render ya Railway automatic PORT environment variable assign karta hai
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
