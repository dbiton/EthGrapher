from web3 import Web3
import pickle
import time
import os

# Public node URL (Example)
public_node_url = 'https://cloudflare-eth.com'

# Connect to the public Ethereum node
web3 = Web3(Web3.HTTPProvider(public_node_url))

# File to store the ledger (in binary pickle format)
ledger_file = 'ethereum_ledger_100GB.pkl'

def connect_to_ethereum_node():
    """Connect to the Ethereum node and return the Web3 instance."""
    if web3.is_connected():
        print("Connected to the Ethereum node")
        return True
    else:
        print("Connection failed")
        return False

def fetch_block(block_num):
    """Fetch a block by its number and return the block details."""
    try:
        block_details = web3.eth.get_block(block_num, full_transactions=True)
        block_data = {
            'number': block_details.number,
            'hash': block_details.hash.hex(),
            'parentHash': block_details.parentHash.hex(),
            'timestamp': block_details.timestamp,
            'miner': block_details.miner,
            'gasUsed': block_details.gasUsed,
            'transactions': [{
                'hash': tx.hash.hex(),
                'from': tx['from'],
                'to': tx['to'],
                'value': tx['value'],
                'gas': tx['gas'],
                'gasPrice': tx['gasPrice'],
                'input': tx['input']
            } for tx in block_details.transactions]
        }
        return block_data
    except Exception as e:
        print(f"Error fetching block {block_num}: {str(e)}")
        return None

def save_block_to_ledger(block_data):
    """Save block data to the ledger file using pickle."""
    with open(ledger_file, 'ab') as f:
        pickle.dump(block_data, f)
    print(f"Saved block {block_data['number']} with {len(block_data['transactions'])} transactions.")

def load_ledger():
    """Load the ledger from the file if it exists."""
    if os.path.exists(ledger_file):
        with open(ledger_file, 'rb') as f:
            try:
                while True:
                    block_data = pickle.load(f)
                    print(f"Loaded block {block_data['number']}, {len(block_data['transactions'])} transactions.")
                    yield block_data
            except EOFError:
                pass  # End of file reached
    else:
        print("No ledger file found.")

def fetch_and_save_blocks():
    """Fetch and save blocks from the latest to the earliest."""
    latest_block = web3.eth.block_number
    print(f"Starting from block: {latest_block}")
    
    n = 100000

    for block_num in range(latest_block, latest_block-n, -1):
        block_data = fetch_block(block_num)
        if block_data:
            save_block_to_ledger(block_data)
        time.sleep(0.1)

if __name__ == "__main__":
    if connect_to_ethereum_node():
        # Fetch and save new blocks
        fetch_and_save_blocks()

        # Load the existing ledger (if any)
        # blocks = [b for b in load_ledger()]
        


