import os
import time
import threading
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv

load_dotenv()

# === ENV VARS ===
BASE_RPC = os.getenv("BASE_RPC")
BASESCAN_API_KEY = os.getenv("BASESCAN_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# === HEALTH CHECK PORT FOR RENDER ===
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    server = HTTPServer(("0.0.0.0", 10000), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_health_server, daemon=True).start()

# === TELEGRAM ALERT ===
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

# === PLACEHOLDER: SCANNER LOGIC ===
def scan_blockchain_loop():
    while True:
        try:
            # You can replace this with your real scan logic
            print("Scanning blockchain...")
            send_telegram("✅ Bot dey alive, scanning...")
            time.sleep(60)  # Run every 60 seconds
        except Exception as e:
            print("Error:", e)
            time.sleep(30)

# === START BOT ===
if __name__ == "__main__":
    scan_blockchain_loop()
