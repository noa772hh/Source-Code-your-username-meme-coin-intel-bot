from fastapi import FastAPI
from web3 import Web3
from dotenv import load_dotenv
import os
import requests
import time
import datetime

load_dotenv()

# === CONFIG ===
RPC = os.getenv("BASE_RPC")  # Use your Base RPC
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BASESCAN_API = os.getenv("BASESCAN_API")

web3 = Web3(Web3.HTTPProvider(RPC))
app = FastAPI()

# === UTILS ===
def send_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Telegram error:", e)

def is_fresh_wallet(wallet):
    try:
        url = f"https://api.basescan.org/api?module=account&action=txlist&address={wallet}&apikey={BASESCAN_API}"
        res = requests.get(url).json()
        txs = res.get("result", [])
        if len(txs) <= 2:
            for tx in txs:
                if "binance" in tx["from"].lower() or "binance" in tx["to"].lower():
                    return True
            return len(txs) == 1
        return False
    except:
        return False

def get_token_age(contract):
    try:
        url = f"https://api.basescan.org/api?module=contract&action=getsourcecode&address={contract}&apikey={BASESCAN_API}"
        res = requests.get(url).json()
        created_at = res["result"][0]["ContractCreationDate"]
        if created_at:
            created_time = datetime.datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S")
            age_days = (datetime.datetime.utcnow() - created_time).days
            return age_days
        return 0
    except:
        return 0

# === BOT MAIN ===
def run_bot():
    print("👀 Watching for fresh wallet buys...")
    last_block = web3.eth.block_number

    while True:
        try:
            latest = web3.eth.block_number
            for blk_num in range(last_block + 1, latest + 1):
                block = web3.eth.get_block(blk_num, full_transactions=True)
                for tx in block.transactions:
                    if tx.to and tx.input and tx.value == 0:
                        wallet = tx["from"]
                        if is_fresh_wallet(wallet):
                            receipt = web3.eth.get_transaction_receipt(tx.hash)
                            for log in receipt.logs:
                                token_address = log.address
                                age = get_token_age(token_address)
                                if age >= 30:
                                    token_symbol = get_token_symbol(token_address)
                                    alert = f"🚨 <b>Fresh Wallet Buy</b>\n\n" \
                                            f"👤 Wallet: <code>{wallet}</code>\n" \
                                            f"💰 Token: <code>{token_symbol}</code>\n" \
                                            f"📅 Age: {age} days\n" \
                                            f"https://basescan.org/address/{wallet}"
                                    send_alert(alert)
            last_block = latest
        except Exception as e:
            print("⚠️ Error:", e)
        time.sleep(5)

# === TOKEN SYMBOL ===
def get_token_symbol(contract):
    try:
        abi = [{"constant": True,"inputs": [],"name": "symbol","outputs": [{"name": "","type": "string"}],"type": "function"}]
        contract_instance = web3.eth.contract(address=contract, abi=abi)
        return contract_instance.functions.symbol().call()
    except:
        return "UNKNOWN"

# === FASTAPI ENDPOINT ===
@app.get("/")
def root():
    return {"status": "Meme Coin Bot dey run 🔥"}

# === RUN ===
if __name__ == "__main__":
    from threading import Thread
    Thread(target=run_bot).start()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
