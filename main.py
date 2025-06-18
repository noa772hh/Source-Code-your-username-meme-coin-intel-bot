import os
import time
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()

# === ENV VARS ===
BASESCAN_API_KEY = os.getenv("BASESCAN_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
seen_tokens = set()

# === TELEGRAM ALERT ===
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=data, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

# === APE.STORE FETCH ===
def fetch_ape_store_tokens():
    try:
        res = requests.get("https://api.ape.store/api/tokens?chain=base", timeout=10)
        return res.json().get("tokens", [])
    except Exception as e:
        print("Token fetch error:", e)
        return []

# === FILTER ===
def is_valid_token(token):
    return (
        token.get("liquidity")
        and float(token["liquidity"]) >= 1000
        and token.get("symbol")
        and token["symbol"].lower() != "null"
        and token.get("ageInDays", 99) <= 5
    )

# === BASESCAN BUYERS ===
def get_buyers(token_addr):
    url = "https://api.basescan.org/api"
    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": token_addr,
        "page": 1,
        "offset": 20,
        "sort": "desc",
        "apikey": BASESCAN_API_KEY
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        txs = res.json().get("result", [])
        return [tx["from"] for tx in txs if tx["to"].lower() == token_addr.lower()]
    except Exception as e:
        print("Buyer fetch error:", e)
        return []

# === SMART WALLET CHECK ===
def is_smart_wallet(addr):
    url = "https://api.basescan.org/api"
    params = {
        "module": "account",
        "action": "tokentx",
        "address": addr,
        "page": 1,
        "offset": 5,
        "sort": "desc",
        "apikey": BASESCAN_API_KEY
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        txs = res.json().get("result", [])
        unique = set([tx["contractAddress"] for tx in txs])
        return len(unique) <= 3
    except:
        return False

# === MAIN LOOP ===
def main_loop():
    while True:
        tokens = fetch_ape_store_tokens()
        for t in tokens:
            if not is_valid_token(t):
                continue

            token_id = t["address"]
            if token_id in seen_tokens:
                continue

            buyers = get_buyers(token_id)
            smart_count = 0
            checked = set()
            for b in buyers:
                if b in checked:
                    continue
                if is_smart_wallet(b):
                    smart_count += 1
                checked.add(b)

            if smart_count >= 2:
                msg = (
                    f"🚨 <b>Smart Wallet Sniper Alert!</b>\n\n"
                    f"🪙 Token: <b>{t['name']}</b> (${t['symbol']})\n"
                    f"📊 Liquidity: ${t['liquidity']} | MCap: ${t['fdv']}\n"
                    f"📅 Age: {t['ageInDays']} day(s) | 👥 Holders: {t.get('holders', 'N/A')}\n\n"
                    f"🧠 {smart_count} smart wallets don buy this token\n"
                    f"🔗 https://ape.store/token/{token_id}"
                )
                send_telegram_message(msg)
                seen_tokens.add(token_id)

        time.sleep(60)

# === HEALTH CHECK ===
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK\nBot is alive")

def start_health_server():
    server = HTTPServer(("0.0.0.0", 10000), HealthHandler)
    server.serve_forever()

# === ACTIVITY PING ===
def scan_blockchain_loop():
    while True:
        try:
            print("Scanning blockchain...")
            send_telegram_message("✅ Bot dey alive, scanning...")
            time.sleep(1800)  # 30 mins
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
