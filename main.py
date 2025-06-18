import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BASESCAN_API_KEY = os.getenv("BASESCAN_API_KEY")

seen_tokens = set()

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, data=data)

def fetch_ape_store_tokens():
    try:
        res = requests.get("https://api.ape.store/api/tokens?chain=base")
        return res.json()["tokens"]
    except:
        return []

def filter_valid_tokens(tokens):
    result = []
    for token in tokens:
        if token["liquidity"] and float(token["liquidity"]) >= 1000:
            if token["symbol"] and token["symbol"].lower() != "null":
                if token["ageInDays"] <= 5:
                    result.append(token)
    return result

def format_token_message(token):
    return (
        f"🪙 *{token['name']}* ({token['symbol']}) | Base\n"
        f"⏳ {token['ageInDays']}d ⋅ 👥 {token['holders']}  ⋅ 👀 {token['watchlistCount']}\n"
        f"👥 Socials: {token['links']}\n"
        f"➖➖➖➖➖➖\n"
        f"✅ Passes automated checks. Does not mean it's safe.\n"
        f"{token['address']}\n\n"
        f"🧢 MCap: {token['fdv']} | ATH: {token['ath']}\n"
        f"💧 Liq: {token['liquidity']} ({token['liquidityPercent']}%)\n"
        f"🏷 Price: {token['price']} ({token['priceChange']}%)\n"
        f"🎚 Volume: {token['volume']} (🅑{token['buys']}/Ⓢ{token['sells']})"
    )

def main_loop():
    while True:
        tokens = fetch_ape_store_tokens()
        fresh = filter_valid_tokens(tokens)
        for token in fresh:
            token_id = token['address']
            if token_id not in seen_tokens:
                msg = format_token_message(token)
                send_telegram_message(msg)
                seen_tokens.add(token_id)
        time.sleep(60)

if __name__ == "__main__":
    main_loop()
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# Your main logic (infinite loop, wallet scan, etc.) stays above...

# Fake web server for Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    server = HTTPServer(("0.0.0.0", 10000), HealthCheckHandler)
    server.serve_forever()

# Start server in background so it doesn't block main loop
threading.Thread(target=run_health_server, daemon=True).start()
