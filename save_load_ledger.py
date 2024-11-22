import os
import pickle
import time
import requests
from web3 import Web3
import queue

public_nodes_urls = [
    "https://cloudflare-eth.com",
    "https://rpc.ankr.com/eth",
    "https://eth-mainnet.public.blastapi.io",
    "https://mainnet.infura.io/v3/61c26b521ed84355864460361fc8ca52",
    "https://eth-mainnet.g.alchemy.com/v2/LXa59vi3WiXQzdnd469is-WafCkdDDss",
    "https://ethereum-mainnet.core.chainstack.com/4033397d5b35d9414e7039efbdae0d45"
]

CHAINSTACK_RPC_URL = "https://ethereum-mainnet.core.chainstack.com/4033397d5b35d9414e7039efbdae0d45"

eth_clients = [Web3(Web3.HTTPProvider(url)) for url in public_nodes_urls]
eth_clients_queue = queue.Queue()
for eth_client in eth_clients:
    eth_clients_queue.put(eth_client)

# File to store the ledger (in binary pickle format)
ledger_file = "eth_200_to_201.pkl"
receipt_file = "rec_20000196_20000472.pkl"
blocks_traces_file = "block_traces.pkl"

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

def fetch_receipt(tx_hash):
    result = None
    web3 = eth_clients_queue.get()
    try:
        result = web3.eth.get_transaction_receipt(tx_hash)
    except Exception as e:
        print(f"Error fetching receipt {tx_hash}: {str(e)}")
    time.sleep(0.1)
    eth_clients_queue.put(web3)
    return result

def get_write_addresses(tx_receipt):
    write_addresses = [log['address'] for log in tx_receipt['logs']]
    return write_addresses

def estimate_read_addresses(tx, write_addresses):
    all_addresses = extract_params_as_addresses(tx)
    write_addresses = filter(lambda v: v not in write_addresses, all_addresses)
    return list(write_addresses)

def extract_params_as_addresses(tx):
    input_data = tx['input'].hex()
    if input_data.startswith('0x'):
        input_data = input_data[2:]
    
    w3 = Web3()

    function_selector = input_data[:8]
    parameter_data = input_data[8:]

    addresses = []
    
    for i in range(0, len(parameter_data), 64):
        chunk = parameter_data[i:i+64]
        
        if len(chunk) >= 40:
            potential_address = '0x' + chunk[-40:]
            
            # Verify and add the checksummed address
            if w3.is_address(potential_address):
                checksummed_address = w3.to_checksum_address(potential_address)
                addresses.append(checksummed_address)
    
    return addresses


def fetch_block(block_num):
    try:
        web3 = eth_clients_queue.get()
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
        time.sleep(0.1)
        eth_clients_queue.put(web3)
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


def load_receipts(block_number):
    receipts = []
    if os.path.exists(receipt_file):
        with open(receipt_file, "rb") as f:
            try:
                while True:
                    curr_block_number, tx_hash, receipt = pickle.load(f)
                    if curr_block_number < block_number:
                        continue
                    if curr_block_number > block_number:
                        return receipts 
                    receipts.append((tx_hash, receipt))
            except EOFError:
                pass  # End of file reached
    else:
        print("No ledger file found.")


def load_blocks_traces(limit=None):
    i = 0
    if os.path.exists(blocks_traces_file):
        with open(blocks_traces_file, "rb") as f:
            try:
                while True:
                    block_number, block_trace = pickle.load(f)
                    i += 1
                    if i == limit:
                        return
                    print(f"Loaded block {block_number}")
                    yield block_number, block_trace
            except EOFError:
                pass  # End of file reached
    else:
        print("No traces file found.")

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

from concurrent.futures import ThreadPoolExecutor, as_completed


def fetch_and_save_blocks():
    for client in eth_clients:
        if not connect_to_ethereum_node(client):
            raise Exception("connection failed")
    
    futures = []
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_block, block_num) for block_num in range(20091474, 20100000, 1)]

        for future in as_completed(futures):
            block_data = future.result()
            if block_data:
                save_block_to_ledger(block_data)


def fetch_block_trace(block_number):
    payload = {
        "jsonrpc": "2.0",
        "method": "debug_traceBlockByNumber",
        "params": [
            hex(block_number),
            {"tracer": "callTracer"}
        ],
        "id": 1
    }
    response = requests.post(CHAINSTACK_RPC_URL, json=payload)
    
    if response.status_code == 200:
        return response.json()["result"]
    else:
        print(f"Error tracing block: {response.text}")


def fetch_tx_trace(tx):
    tx_hash = f"0x{tx['hash']}"
    """Trace a transaction to get read/write addresses."""
    payload = {
        "jsonrpc": "2.0",
        "method": "debug_traceTransaction",
        "params": [tx_hash, {"tracer": "callTracer"}],
        "id": 1
    }
    response = requests.post(CHAINSTACK_RPC_URL, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error tracing transaction: {response.text}")

def fetch_and_save_recepits():
    for client in eth_clients:
        if not connect_to_ethereum_node(client):
            raise Exception("connection failed")

    start = 20002000
    end = 20100000
    step = 1000
    for curr in range(start, end, step):
        with ThreadPoolExecutor() as executor:
            futures = []
            for block in load_ledger():
                if block['number'] <= curr:
                    continue
                if block['number'] >= curr + step:
                    break
                for i, tx in enumerate(block['transactions']):
                    if is_smart_contract_interaction(tx) or is_smart_contract_deployment(tx):
                        futures.append(executor.submit(fetch_receipt, tx["hash"]))
                        print(f"{block['number']} submitted {i}/{len(block['transactions'])}")

            with open(receipt_file, "ab") as f:
                print("writing to file...")
                for future in as_completed(futures):
                    receipt = future.result()
                    print(receipt["blockNumber"])
                    pickle.dump(receipt, f)

def sort_blocks():
    blocks = []
    for block in load_ledger():
        blocks.append(block)
    blocks.sort(key=lambda block: block["number"])
    with open("sorted.pkl", "ab") as f:
        print("writing to file...")
        for block in blocks:
            print(block["number"])
            pickle.dump(block, f)