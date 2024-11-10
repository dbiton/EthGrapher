import os
import pickle
import time
from web3 import Web3


public_nodes_urls = [
    "https://cloudflare-eth.com",
    "https://rpc.ankr.com/eth",
    "https://eth-mainnet.public.blastapi.io"
]

eth_clients = [Web3(Web3.HTTPProvider(url)) for url in public_nodes_urls]


# File to store the ledger (in binary pickle format)
ledger_file = "ethereum_ledger.pkl"


def connect_to_ethereum_node(web3):
    """Connect to the Ethereum node and return the Web3 instance."""
    if web3.is_connected():
        print("Connected to Ethereum node")
        return True
    else:
        print("Connection failed")
        return False


def fetch_block(web3, block_num):
    """Fetch a block by its number and return the block details."""
    try:
        block_details = web3.eth.get_block(block_num, full_transactions=True)
        block_data = {
            "number": block_details.number,
            "hash": block_details.hash.hex(),
            "parentHash": block_details.parentHash.hex(),
            "timestamp": block_details.timestamp,
            "miner": block_details.miner,
            "gasUsed": block_details.gasUsed,
            "transactions": [
                {
                    "hash": tx.hash.hex(),
                    "from": tx["from"],
                    "to": tx["to"],
                    "value": tx["value"],
                    "gas": tx["gas"],
                    "gasPrice": tx["gasPrice"],
                    "input": tx["input"],
                }
                for tx in block_details.transactions
            ],
        }
        return block_data
    except Exception as e:
        print(f"Error fetching block {block_num}: {str(e)}")
        return None


def save_block_to_ledger(block_data):
    """Save block data to the ledger file using pickle."""
    with open(ledger_file, "ab") as f:
        pickle.dump(block_data, f)
    print(
        f"Saved block {block_data['number']} with {len(block_data['transactions'])} transactions."
    )


def load_ledger(limit=None):
    """Load the ledger from the file if it exists."""
    i = 0
    if os.path.exists(ledger_file):
        with open(ledger_file, "rb") as f:
            try:
                while True:
                    block_data = pickle.load(f)
                    if len(block_data['transactions']) == 0:
                        continue
                    i += 1
                    if i == limit:
                        return
                    print(
                        f"Loaded block {block_data['number']}, {len(block_data['transactions'])} transactions."
                    )
                    yield block_data
            except EOFError:
                pass  # End of file reached
    else:
        print("No ledger file found.")


def fetch_and_save_blocks():
    for client in eth_clients:
        if not connect_to_ethereum_node(client):
            raise Exception("connection failed")
    
    for block_num in range(20100000, 20200000, 1):
        block_data = fetch_block(eth_clients[block_num%len(eth_clients)], block_num)
        if block_data:
            save_block_to_ledger(block_data)
        # time.sleep(0.1)
