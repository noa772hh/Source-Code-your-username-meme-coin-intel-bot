from fastapi import FastAPI
import os
from web3 import Web3
from dotenv import load_dotenv
import uvicorn

load_dotenv()

RPC = os.getenv("BLAST_RPC")  # Use your RPC from .env
web3 = Web3(Web3.HTTPProvider(RPC))

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Meme Coin Bot dey run 🔥"}

def run_bot():
    print("Meme coin bot started...")
    latest_block = web3.eth.block_number
    print(f"Latest block: {latest_block}")

if __name__ == "__main__":
    run_bot()
    uvicorn.run(app, host="0.0.0.0", port=10000)
