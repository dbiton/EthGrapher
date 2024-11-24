from matplotlib import pyplot as plt
import pandas as pd
import networkx as nx
import multiprocessing as mp

from save_load_ledger import *
from graph_stats import *

def process_call(call, reads, writes):
    # Handle STATICCALL: Read-only call
    if call["type"] == "STATICCALL":
        reads.add(call["to"])

    # Handle CALL, CREATE, and DELEGATECALL
    elif call["type"] in {"CALL", "CREATE", "DELEGATECALL"}:
        # DELEGATECALL writes to the caller's context, not `to`
        if call["type"] == "DELEGATECALL":
            writes.add(call["from"])
        else:
            writes.add(call["to"])

        # Value transfer always indicates a write to the recipient
        if "value" in call and int(call["value"], 16) > 0:
            writes.add(call["to"])

        # The caller may also modify its own state
        writes.add(call["from"])
    
    if "calls" in call:
        for sub_call in call["calls"]:
            process_call(sub_call, reads, writes)

def extract_reads_writes_from_block(block_trace):
    ops = []

    # Process each transaction in the block trace
    for entry in block_trace:
        tx = entry['result']
        tx_hash = entry['txHash']
        if "calls" in tx:
            for call in tx["calls"]:
                reads = set()
                writes = set()
                process_call(call, reads, writes)
                ops += [{"hash": tx_hash, "address": address, "op": "read"} for address in reads]
                ops += [{"hash": tx_hash, "address": address, "op": "write"} for address in writes]

    return ops

def create_conflict_graph_block_trace(block_trace):
    G = nx.Graph()

    ops = extract_reads_writes_from_block(block_trace)

    for tx in block_trace:
        G.add_node(tx['txHash'])

    for i, t1 in enumerate(ops):
        for t2 in ops[i+1:]:
            if t1["hash"] == t2["hash"]:
                continue

            if (t1["address"] == t2["address"]
                and (t1["op"] == "write" or t2["op"] == "write")):
                G.add_edge(t1["hash"], t2["hash"])
    return G


def create_conflict_graph_trace(block):
    txs = block["transactions"]
    # Initialize a graph
    G = nx.Graph()

    for tx in txs:
        G.add_node(tx['hash'])

    ops = []
    # Add nodes for each transaction
    for tx in txs:
        ops.append({"hash": tx['hash'], "data": tx['from'], "op": 'write'})
        ops.append({"hash": tx['hash'], "data": tx['to'], "op": 'write'})

    # Check for conflicts and add edges
    for i, t1 in enumerate(ops):
        for j, t2 in enumerate(ops):
            if t1["hash"] == t2["hash"]:
                continue  # Avoid duplicate pairs and self-loops

            # Conflict if same source or destination with at least one write
            if (
                t1["data"] == t2["data"]
                and (t1["op"] == "write" or t2["op"] == "write")
            ):
                G.add_edge(t1["hash"], t2["hash"])
    return G


def plot_graph(graph):
    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(graph)  # positions for all nodes
    nx.draw(graph, pos, arrows=True)
    plt.title("Directed Graph Visualization")
    plt.show()

def process_block(block_number, block_trace):
    """Process a single block and return results."""
    conflict_graph = create_conflict_graph_block_trace(block_trace)
    
    results = {
        "blockNumber": block_number,
        "txs": len(block_trace),
        "degree": graph_average_degree(conflict_graph),
        "greedy_color": graph_greedy_coloring(conflict_graph),
        "assortativity": graph_assortativity(conflict_graph),
        "cluster_coe": graph_cluster_coe(conflict_graph),
        "density": graph_density(conflict_graph),
        "modularity": graph_modularity(conflict_graph),
        "transitivity": graph_transitivity(conflict_graph),
        "diameter": graph_diameter(conflict_graph),
        "clique_number": graph_clique(conflict_graph),
        "conflict_percentage": graph_conflict_percentage(conflict_graph)
    }
    return results

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata

def plot_data():
    lines_count = 5
    bins_count = 64

    # Load the CSV file
    file_path = "eth_stats.csv"  # Replace with your file path
    df = pd.read_csv(file_path)

    # Ensure the data has X, Y, and other columns
    if "conflict_percentage" not in df.columns or "txs" not in df.columns:
        raise ValueError("The CSV file must contain 'X' and 'Y' columns.")

    # Extract X, Y, and property columns
    properties = df.drop(columns=["conflict_percentage", "txs"]).columns
    
    split_values = df["txs"].quantile([i / (lines_count + 1) for i in range(1, lines_count + 1)])
    split_values = sorted(list(split_values))
    # Create heatmaps for each property
    for prop in properties:
        plt.figure(figsize=(8, 6))
        for i_tx_group in range(len(split_values) + 1):
            if i_tx_group == 0:
                txs_min = 0
                txs_max = split_values[i_tx_group]
            elif i_tx_group == len(split_values):
                txs_min = split_values[i_tx_group - 1]
                txs_max = float('inf')
            else:
                txs_min = split_values[i_tx_group - 1]
                txs_max = split_values[i_tx_group]

            # Select the data for the current tx_group
            df_group = df.loc[(df["txs"] < txs_max) & (df["txs"] > txs_min)].sort_values(by=prop)
            
            # Copy to avoid SettingWithCopyWarning
            df_group = df_group.copy()
            
            prop_data = df_group[prop]
            conflict_percentage = df_group["conflict_percentage"]
            
            # Bin the 'prop' data
            bins = np.linspace(prop_data.min(), prop_data.max(), num=bins_count)  # Adjust 'num' for bin granularity
            df_group['prop_bin'] = pd.cut(prop_data, bins=bins, include_lowest=True)
            
            # Group by the bins and compute mean and SEM
            grouped = df_group.groupby('prop_bin')
            mean_prop_data = grouped[prop].mean()
            mean_conflict = grouped['conflict_percentage'].mean()
            sem_conflict = grouped['conflict_percentage'].sem()  # Standard Error of the Mean
            
            # Plot mean conflict_percentage with confidence intervals
            plt.plot(mean_prop_data, mean_conflict, label=f"#txs>{int(txs_min)}")
            plt.fill_between(mean_prop_data,
                            mean_conflict - sem_conflict,
                            mean_conflict + sem_conflict,
                            alpha=0.2)  # Adjust 'alpha' for transparency
            
        plt.grid()
        plt.title(f"{prop}")
        plt.xlabel(f"{prop}")
        plt.ylabel("conflict_percentage")
        plt.tight_layout()
        plt.legend()

        # Save the plot
        plt.savefig(f"scatter_{prop}.png")
        plt.close()

    print("Heatmaps have been generated and saved as PNG files.")

def process_blocks_traces():
    data = []
    # Create a pool of worker processes
    with mp.Pool() as pool:
        # Use a list to store async results
        async_results = []

        # Load blocks from the ledger using the generator
        for block_number, block_trace in load_blocks_traces():
            # Submit each block for processing
            async_result = pool.apply_async(process_block, (block_number, block_trace,))
            async_results.append(async_result)

        # Collect results as they complete
        for i, async_result in enumerate(async_results):
            result = async_result.get()  # This will block until the result is ready
            data.append(result)
            print(i, result)

        props = list([k for k in data[0].keys() if k != "conflict_percentage" and k != "hash"])

        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(data)

        df.to_csv("eth_stats.csv", index=False)

        agg_dict = {f'avg_{key}': (key, 'mean') for key in props}

        average_results = df.groupby('txs').agg(**agg_dict).reset_index()

    for key in props:
        avg_key = f'avg_{key}'
        
        # Create a new figure for each key
        fig, ax = plt.subplots(figsize=(6, 4))
        
        # Plot the data for the current key
        ax.plot(average_results['txs'], average_results[avg_key], label=f'Average {key.capitalize()}', marker='o')
        ax.set_title(f'{key.capitalize()}')
        ax.set_xlabel('Number of Transactions')
        ax.set_ylabel(f'Average {key}')
        ax.set_xscale('log')
        ax.grid(True)
        
        # Display the plot
        plt.show()
        
        # Save the plot as a PNG file with the key name
        fig.savefig(f"{key}.png")
        
        # Close the figure to free up memory
        plt.close(fig)

def main():
    # process_blocks_traces()
    plot_data()

if __name__ == "__main__":
    main()