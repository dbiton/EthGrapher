from matplotlib import pyplot as plt
import pandas as pd
from web3 import Web3
import networkx as nx
import multiprocessing as mp

from collections import defaultdict
import pickle
import time
import os

# Public node URL (Example)
public_node_url = "https://cloudflare-eth.com"

# Connect to the public Ethereum node
web3 = Web3(Web3.HTTPProvider(public_node_url))

# File to store the ledger (in binary pickle format)
ledger_file = "ethereum_ledger_100GB.pkl"


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


def txs_as_graph(txs: list):
    G = nx.DiGraph()
    edges = []
    for tx in txs:
        from_account = tx["from"]
        to_account = tx["to"]
        if from_account is None or to_account is None:
            continue
        edges.append((from_account, to_account))
    G.add_edges_from(edges)
    return G


def fetch_and_save_blocks():
    """Fetch and save blocks from the latest to the earliest."""
    latest_block = web3.eth.block_number
    print(f"Starting from block: {latest_block}")

    for block_num in range(latest_block, -1, -1):
        block_data = fetch_block(block_num)
        if block_data:
            save_block_to_ledger(block_data)
        time.sleep(0.1)


def create_conflict_graph(block):
    txs = block["transactions"]
    # Initialize a graph
    G = nx.Graph()

    # Add nodes for each transaction
    for transaction in txs:
        G.add_node(transaction["hash"], **transaction)

    # Check for conflicts and add edges
    for i, t1 in enumerate(txs):
        for j, t2 in enumerate(txs):
            if i >= j:
                continue  # Avoid duplicate pairs and self-loops

            # Conflict if same source or destination with at least one write
            if (
                t1["from"] == t2["from"]
                or t1["to"] == t2["to"]
                or t1["from"] == t2["to"]
                or t1["to"] == t2["from"]
            ):
                G.add_edge(t1["hash"], t2["hash"])
    return G


def graph_average_degree(graph):
    num_edges = graph.number_of_edges()
    num_nodes = graph.number_of_nodes()
    if num_nodes == 0:
        return 0.0  # Avoid division by zero if there are no nodes
    avg_degree = (2 * num_edges) / num_nodes
    return avg_degree


def graph_has_cycle(graph):
    try:
        # Try to find cycles using depth-first search
        cycle = nx.find_cycle(graph, orientation="original")
        return True
    except nx.NetworkXNoCycle:
        return False


def graph_longest_path_length(graph):
    # Convert the undirected graph to a directed one by removing cycles
    dag = nx.DiGraph()
    dag.add_edges_from(graph.edges())

    # Perform topological sorting
    topo_order = list(nx.topological_sort(dag))

    # Initialize distances to all nodes as negative infinity
    distance = {node: float("-inf") for node in dag.nodes()}
    # Distance to the starting node is 0
    for node in topo_order:
        if distance[node] == float("-inf"):
            distance[node] = 0

        for neighbor in dag.neighbors(node):
            if distance[neighbor] < distance[node] + 1:
                distance[neighbor] = distance[node] + 1

    # The longest path length will be the maximum distance
    if len(distance) == 0:
        return 0
    return max(distance.values())


def plot_graph(graph):
    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(graph)  # positions for all nodes
    nx.draw(graph, pos, arrows=True)
    plt.title("Directed Graph Visualization")
    plt.show()

def process_block(block):
    """Process a single block and return results."""
    conflict_graph = create_conflict_graph(block)
    coloring = nx.coloring.greedy_color(conflict_graph, strategy="largest_first")
    colors_count = len(set(coloring.values()))
    avg_degree = graph_average_degree(conflict_graph)
    count_transactions = len(block["transactions"])
    
    # longest_path_length = float("inf")
    # Uncomment the following if you want to check for cycles and calculate the longest path
    # if not graph_has_cycle(conflict_graph):
    longest_path_length = graph_longest_path_length(conflict_graph)
    
    results = {
        "txs": count_transactions,
        "degree": avg_degree,
        "colors": colors_count,
        "path": longest_path_length,
    }
    return results

if __name__ == "__main__":
    if connect_to_ethereum_node():
        # Fetch and save new blocks
        # fetch_and_save_blocks()

        # Load the existing ledger (if any)

            data = []

    # Create a pool of worker processes
    with mp.Pool(mp.cpu_count()) as pool:
        # Use a list to store async results
        async_results = []

        # Load blocks from the ledger using the generator
        for block in load_ledger(100000):
            # Submit each block for processing
            async_result = pool.apply_async(process_block, (block,))
            async_results.append(async_result)

        # Collect results as they complete
        for i, async_result in enumerate(async_results):
            result = async_result.get()  # This will block until the result is ready
            data.append(result)
            print(i, result)

        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(data)

        # Group by the number of transactions and calculate the average degree and colors
        average_results = df.groupby('txs').agg(
            avg_degree=('degree', 'mean'),
            avg_colors=('colors', 'mean'),
            avg_path = ('path', 'mean')
        ).reset_index()

        # Create a figure with two subplots
        fig, axs = plt.subplots(1, 3, figsize=(10, 12))

        # Plot average degree
        axs[0].plot(average_results['txs'], average_results['avg_degree'], label='Average Degree', marker='o', color='blue')
        axs[0].set_title('Average Degree vs Number of Transactions')
        axs[0].set_xlabel('Number of Transactions')
        axs[0].set_ylabel('Average Degree')
        axs[0].set_yscale('log')
        axs[0].grid(True)

        # Plot average number of colors
        axs[1].plot(average_results['txs'], average_results['avg_colors'], label='Average Colors', marker='o', color='orange')
        axs[1].set_title('Average Colors vs Number of Transactions')
        axs[1].set_xlabel('Number of Transactions')
        axs[1].set_ylabel('Average Colors')
        axs[1].set_yscale('log')
        axs[1].grid(True)

        # Plot average number of colors
        axs[2].plot(average_results['txs'], average_results['avg_path'], label='Average Path', marker='o', color='green')
        axs[2].set_title('Average Longest Path vs Number of Transactions')
        axs[2].set_xlabel('Number of Transactions')
        axs[2].set_ylabel('Average Longest Path')
        axs[2].set_yscale('log')
        axs[2].grid(True)

        # Adjust layout and show the plots
        plt.show()