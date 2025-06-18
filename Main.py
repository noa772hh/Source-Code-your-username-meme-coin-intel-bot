import os
import time
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
seen_tokens = set()

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Telegram Error:", e)

def fetch_tokens():
    try:
        res = requests.get("https://api.ape.store/api/tokens?chain=base")
        return res.json()["tokens"]
    except Exception as e:
        print("Fetch Error:", e)
        return []

def filter_token(t):
    try:
        age = int(t["age"].split(" ")[0])
        return (
            t.get("symbol") and 
            t.get("liquidity") and 
            float(t["liquidity"]) >= 1000 and 
            age <= 5
        )
    except:
        return False

def main_loop():
    while True:
        tokens = fetch_tokens()
        for token in tokens:
            token_id = token.get("address")
            if token_id in seen_tokens:
                continue
            if filter_token(token):
                seen_tokens.add(token_id)
                msg = f"🚨 <b>{token['name']} ({token['symbol']})</b>\n🔗 <a href='https://basescan.org/token/{token_id}'>View on BaseScan</a>\n💧 Liquidity: ${token['liquidity']}"
                send_telegram(msg)
        time.sleep(60)

class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Alive")

if __name__ == "__main__":
    import threading
    threading.Thread(target=lambda: HTTPServer(("0.0.0.0", 10000), HealthCheck).serve_forever(), daemon=True).start()
    send_telegram("✅ Smart wallet alert bot don start...")
    main_loop()
