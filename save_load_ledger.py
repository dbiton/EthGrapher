import os
import pickle
import random
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

def has_field(tx, field):
    return field in tx and tx[field] != b'' and tx[field] != None

def is_smart_contract_deployment(tx):
    return has_field(tx, "input") and not has_field(tx, 'to')

def is_smart_contract_interaction(tx):
    return has_field(tx, "input") and has_field(tx, 'to')

def fetch_receipt(tx):
    web3 = random.choice(eth_clients)
    tx_hash = tx['hash']
    return web3.eth.get_transaction_receipt(tx_hash)

def get_write_addresses(tx_receipt):
    write_addresses = [log['address'] for log in tx_receipt['logs']]
    return write_addresses

def estimate_read_addresses(tx, write_addresses):
    all_addresses = extract_params_as_addresses(tx)
    write_addresses = filter(lambda v: v not in write_addresses, all_addresses)
    return list(write_addresses)

def extract_params_as_addresses(tx):
    input_data = tx['input']
    if input_data.startswith('0x'):
        input_data = input_data[2:]
    
    if len(input_data) % 64 != 0:
        raise ValueError("Input data length is not valid. It should be a multiple of 32 bytes.")
    
    w3 = Web3()

    function_selector = input_data[:8]
    parameter_data = input_data[8:]
    
    addresses = []
    
    for i in range(0, len(parameter_data), 64):
        chunk = parameter_data[i:i+64]
        
        potential_address = '0x' + chunk[-40:]
        
        if w3.isAddress(potential_address):
            checksummed_address = w3.toChecksumAddress(potential_address)
            addresses.append(checksummed_address)
    
    return addresses

def fetch_block(web3, block_num):
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
