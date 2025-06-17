from web3 import Web3
import requests
import time
import json

# ✅ BASE RPC (you fit change to your own)
RPC_URL = "https://base-mainnet.public.blastapi.io"
web3 = Web3(Web3.HTTPProvider(RPC_URL))

# ✅ Telegram
TELEGRAM_BOT_TOKEN = "8063951651:AAH6P50PWHjXU32SG4n1qo9GrUCjWM4fxOk"
TELEGRAM_CHAT_ID = "7381896550"

# ✅ Fresh wallet threshold
MAX_TX_COUNT = 3

# ✅ Alert function
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram Error:", e)

# ✅ Track latest block
latest_block = web3.eth.block_number
print("👀 Watching for fresh wallet buys...")

while True:
    try:
        block = web3.eth.get_block(latest_block, full_transactions=True)
        for tx in block.transactions:
            if tx.to:
                # Check if fresh wallet
                tx_count = web3.eth.get_transaction_count(tx['from'])
                if tx_count <= MAX_TX_COUNT:
                    msg = f"🚨 Fresh Wallet Detected!\n\n👜 Wallet: {tx['from']}\n📦 Bought Token or Sent TX to: {tx['to']}\n🔗 Block: {latest_block}"
                    send_telegram_alert(msg)
        latest_block += 1
    except Exception as e:
        print("Error:", e)
        time.sleep(3)
