# маленький веб-сервер, чтобы Replit не засыпал
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.get("/")
def home():
    return "OK", 200

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()
