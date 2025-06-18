import os
import time
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()

# === ENV VARS ===
BASE_RPC = os.getenv("BASE_RPC")
BASESCAN_API_KEY = os.getenv("BASESCAN_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
seen_tokens = set()

# === TELEGRAM ALERT ===
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

# === APE.STORE FETCH ===
def fetch_ape_store_tokens():
    try:
        res = requests.get("https://api.ape.store/api/tokens?chain=base")
        return res.json().get("tokens", [])
    except Exception as e:
        print("Error fetching tokens:", e)
        return []

def filter_valid_tokens(tokens):
    result = []
    for token in tokens:
        if (
            token.get("liquidity") and float(token["liquidity"]) >= 1000 and
            token.get("symbol") and token["symbol"].lower() != "null" and
            token.get("ageInDays", 99) <= 5
        ):
            result.append(token)
    return result

def format_token_message(token):
    return (
        f"🪙 *{token['name']}* ({token['symbol']}) | Base\n"
        f"⏳ {token['ageInDays']}d ⋅ 👥 {token['holders']}  ⋅ 👀 {token['watchlistCount']}\n"
        f"🔗 {token['links']}\n"
        f"➖➖➖➖➖➖\n"
        f"✅ Passes basic checks. Not financial advice.\n"
        f"{token['address']}\n\n"
        f"🧢 MCap: {token['fdv']} | ATH: {token['ath']}\n"
        f"💧 Liq: {token['liquidity']} ({token['liquidityPercent']}%)\n"
        f"🏷 Price: {token['price']} ({token['priceChange']}%)\n"
        f"🎚 Volume: {token['volume']} (🅑{token['buys']}/Ⓢ{token['sells']})"
    )

# === APE.STORE MONITOR LOOP ===
def main_loop():
    while True:
        tokens = fetch_ape_store_tokens()
        fresh_tokens = filter_valid_tokens(tokens)
        for token in fresh_tokens:
            token_id = token["address"]
            if token_id not in seen_tokens:
                msg = format_token_message(token)
                send_telegram_message(msg)
                seen_tokens.add(token_id)
        time.sleep(60)

# === HEALTH CHECK WEB SERVER FOR RENDER ===
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK\nBot is alive")

def start_health_server():
    server = HTTPServer(("0.0.0.0", 10000), HealthHandler)
    server.serve_forever()

# === JUST TO SHOW BOT IS RUNNING ===
def scan_blockchain_loop():
    while True:
        try:
            print("Scanning blockchain...")
            send_telegram_message("✅ Bot dey alive, scanning...")
            time.sleep(60)
        except Exception as e:
            print("Error:", e)
            time.sleep(30)

# === START EVERYTHING ===
if __name__ == "__main__":
    threading.Thread(target=scan_blockchain_loop, daemon=True).start()
    threading.Thread(target=main_loop, daemon=True).start()
    threading.Thread(target=start_health_server, daemon=True).start()

    send_telegram_message("✅ Ape.store bot don start, scanning Base...")

    while True:
        time.sleep(60)
