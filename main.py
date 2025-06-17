import os
import requests
import time
from web3 import Web3
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BASESCAN_API_KEY = os.getenv("BASESCAN_API_KEY")
BASE_RPC = os.getenv("BASE_RPC")

web3 = Web3(Web3.HTTPProvider(BASE_RPC))
CHECKED_TXS = set()

print("👀 Watching for fresh wallet buys...")

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"❌ Telegram error: {e}")

def is_wallet_fresh(wallet_address):
    url = f"https://api.basescan.org/api?module=account&action=txlist&address={wallet_address}&apikey={BASESCAN_API_KEY}"
    try:
        res = requests.get(url).json()
        txs = res["result"]
        if len(txs) <= 2:
            return True
        return False
    except:
        return False

def get_token_info(token_address):
    url = f"https://api.basescan.org/api?module=token&action=tokeninfo&contractaddress={token_address}&apikey={BASESCAN_API_KEY}"
    try:
        res = requests.get(url).json()
        result = res["result"]
        name = result.get("name", "")
        symbol = result.get("symbol", "")
        decimals = int(result.get("decimals", 18))
        created_time = datetime.utcfromtimestamp(int(result.get("createdAt", 0)))
        age_days = (datetime.utcnow() - created_time).days
        return name, symbol, age_days
    except:
        return None, None, 0

def process_tx(tx):
    if tx["hash"] in CHECKED_TXS:
        return
    CHECKED_TXS.add(tx["hash"])

    to = tx["to"]
    from_addr = tx["from"]

    if not to or not from_addr:
        return

    if not is_wallet_fresh(from_addr):
        return

    name, symbol, age = get_token_info(to)
    if not symbol or age < 30:
        return

    message = (
        f"🚨 *Fresh Wallet Buy Alert!*\n\n"
        f"• Wallet: [{from_addr}](https://basescan.org/address/{from_addr})\n"
        f"• Token: [{symbol}](https://basescan.org/token/{to})\n"
        f"• Age: {age} days\n"
        f"• TX: [View TX](https://basescan.org/tx/{tx['hash']})"
    )
    send_telegram_alert(message)
    print(f"✅ Alert sent for {symbol} by {from_addr}")

def monitor_blocks():
    last_block = web3.eth.block_number
    while True:
        current_block = web3.eth.block_number
        if current_block > last_block:
            for block_num in range(last_block + 1, current_block + 1):
                block = web3.eth.get_block(block_num, full_transactions=True)
                for tx in block.transactions:
                    process_tx(tx)
            last_block = current_block
        time.sleep(2)

if __name__ == "__main__":
    monitor_blocks()
