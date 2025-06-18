import os
import time
import requests
from dotenv import load_dotenv
from datetime import datetime
from web3 import Web3

load_dotenv()

BASE_RPC = os.getenv("BASE_RPC") or "https://rpc.ankr.com/base"
BASESCAN_API_KEY = os.getenv("BASESCAN_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

web3 = Web3(Web3.HTTPProvider(BASE_RPC))
CHECKED_TXS = set()
MAX_TX_COUNT = 2  # Fresh wallet max TXs

def send_alert(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "parse_mode": "HTML"
        })
    except Exception as e:
        print("Telegram Error:", e)

def is_fresh_wallet(wallet):
    try:
        url = f"https://api.basescan.org/api?module=account&action=txlist&address={wallet}&apikey={BASESCAN_API_KEY}"
        res = requests.get(url).json()
        txs = res.get("result", [])
        return len(txs) <= MAX_TX_COUNT
    except:
        return False

def get_token_info(address):
    try:
        url = f"https://api.basescan.org/api?module=token&action=tokeninfo&contractaddress={address}&apikey={BASESCAN_API_KEY}"
        res = requests.get(url).json().get("result", {})
        name = res.get("name", "")
        symbol = res.get("symbol", "")
        created = int(res.get("createdAt", "0"))
        if not symbol or created == 0:
            return None, None, 0
        age_days = (datetime.utcnow() - datetime.utcfromtimestamp(created)).days
        return name, symbol, age_days
    except:
        return None, None, 0

def process_tx(tx):
    if tx["hash"] in CHECKED_TXS:
        return
    CHECKED_TXS.add(tx["hash"])

    from_addr = tx["from"]
    to_addr = tx["to"]
    if not to_addr or not from_addr:
        return
    if not is_fresh_wallet(from_addr):
        return
    name, symbol, age = get_token_info(to_addr)
    if not symbol or age < 30:
        return

    msg = (
        f"🚨 <b>Fresh Wallet Buy Alert</b>\n\n"
        f"👜 <b>Wallet:</b> <a href='https://basescan.org/address/{from_addr}'>{from_addr}</a>\n"
        f"💊 <b>Token:</b> <a href='https://basescan.org/token/{to_addr}'>{symbol}</a>\n"
        f"📅 <b>Token Age:</b> {age} days\n"
        f"🔗 <b>TX:</b> <a href='https://basescan.org/tx/{tx['hash']}'>View TX</a>"
    )
    send_alert(msg)
    print("✅ Sent alert for", symbol)

def monitor():
    last_block = web3.eth.block_number
    print("👀 Watching for fresh wallet buys...")
    while True:
        block = web3.eth.get_block(last_block, full_transactions=True)
        for tx in block.transactions:
            process_tx(tx)
        last_block += 1
        time.sleep(2)

if __name__ == "__main__":
    monitor()
