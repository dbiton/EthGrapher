from matplotlib import pyplot as plt
import pandas as pd
import networkx as nx
import multiprocessing as mp

from parsers import create_conflict_graph, parse_callTracer_trace, parse_preStateTracer_trace
from save_load_ledger import *
from graph_stats import *


def plot_graph(graph):
    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(graph)  # positions for all nodes
    nx.draw(graph, pos, arrows=True)
    plt.title("Directed Graph Visualization")
    plt.show()

def process_block(block_number, block_trace):
    """Process a single block and return results."""
    reads, writes = parse_callTracer_trace(block_trace)
    conflict_graph = create_conflict_graph(reads, writes)
    
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
        "conflict_percentage": graph_conflict_percentage(conflict_graph),
        "largest_conn_comp": graph_largest_connected_component_size(conflict_graph),
        "longest_path_length_monte_carlo": graph_longest_path_length(conflict_graph)
    }
    return results

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata

def plot_data():
    lines_count = 5
    bins_count = 32
    quant_fill = 0.05

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
            bins = np.linspace(conflict_percentage.min(), conflict_percentage.max(), num=bins_count)  # Adjust 'num' for bin granularity
            df_group['conflict_percentage_bin'] = pd.cut(conflict_percentage, bins=bins, include_lowest=True)
            
            # Group by the bins and compute mean and SEM
            grouped = df_group.groupby('conflict_percentage_bin')
            mean_conflict = grouped["conflict_percentage"].mean()
            mean_prop = grouped[prop].mean()
            
            low_prop = grouped[prop].quantile(quant_fill)
            hi_prop = grouped[prop].quantile(1-quant_fill)

            # Plot mean conflict_percentage with confidence intervals
            plt.plot(mean_conflict, mean_prop, label=f"#txs>{int(txs_min)}")
            plt.fill_between(mean_conflict,
                            low_prop,
                            hi_prop,
                            alpha=0.2)  # Adjust 'alpha' for transparency
            
        plt.grid()
        plt.title(f"{prop}")
        plt.ylabel(f"{prop}")
        plt.xlabel("conflict_percentage")
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
        for block_number, block_trace in load_blocks_traces(50000):
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
        # plt.show()
        
        # Save the plot as a PNG file with the key name
        fig.savefig(f"{key}.png")
        
        # Close the figure to free up memory
        # plt.close(fig)

def f(i_begin):
    with open(f"{i_begin}_preState_diffFalse.txt", "ab") as f:
        for i in range(i_begin, i_begin+100000):
            trace = fetch_block_trace(i)
            pickle.dump((i, trace), f)
            print(i)
    return True

def main():
    # Generate the range of inputs
    inputs = range(20000000, 21200000, 100000)
    
    # Set the number of processes (adjust based on your system's cores)
    num_processes = 4
    
    # Use a Pool for multiprocessing
    with mp.Pool(processes=num_processes) as pool:
        # Execute the function `f` across inputs
        results = pool.map(f, inputs)
    
    # Optionally, process the results
    print("Processing completed.")

if __name__ == "__main__":
    diffTrues = []
    diffFalses = []
    with open('20700000_preState_diffTrue.txt', 'rb') as f:
        while True:
            try:
                block_number, trace = pickle.load(f)
                diffTrues.append(trace)
                print(block_number)
            except:
                break
    last_block_number = block_number
    with open('20700000_preState_diffFalse.txt', 'rb') as f:
        for i in range(20700000, last_block_number+1):
            block_number, trace = pickle.load(f)
            print(block_number)
            diffFalses.append(trace)
    for diffFalse, diffTrue in zip(diffFalses, diffTrues):
        reads, writes = parse_preStateTracer_trace(diffFalse, diffTrue)
        G = create_conflict_graph(reads, writes)
        plot_graph(G)