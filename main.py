from matplotlib import pyplot as plt
import pandas as pd
import networkx as nx
import multiprocessing as mp

from save_load_ledger import *
from graph_stats import *


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


def plot_graph(graph):
    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(graph)  # positions for all nodes
    nx.draw(graph, pos, arrows=True)
    plt.title("Directed Graph Visualization")
    plt.show()

def process_block(block):
    """Process a single block and return results."""
    conflict_graph = create_conflict_graph(block)
    
    results = {
        "txs": len(block["transactions"]),
        "degree": graph_average_degree(conflict_graph),
        "colors": graph_coloring(conflict_graph),
        "assortativity": graph_assortativity(conflict_graph),
        "cluster_coe": graph_cluster_coe(conflict_graph),
        "density": graph_density(conflict_graph),
        "edge_con": graph_edge_connectivity(conflict_graph),
        "modularity": graph_modularity(conflict_graph),
        "transitivity": graph_transitivity(conflict_graph),
        "diameter": graph_diameter(conflict_graph)
    }
    return results

if __name__ == "__main__":
    data = []
    
    # Create a pool of worker processes
    with mp.Pool(mp.cpu_count()) as pool:
        # Use a list to store async results
        async_results = []

        # Load blocks from the ledger using the generator
        for block in load_ledger(1000):
            # Submit each block for processing
            async_result = pool.apply_async(process_block, (block,))
            async_results.append(async_result)

        # Collect results as they complete
        for i, async_result in enumerate(async_results):
            result = async_result.get()  # This will block until the result is ready
            data.append(result)
            print(i, result)

        props = list([k for k in data[0].keys() if k != "txs"])

        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(data)

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
        ax.grid(True)
        
        # Display the plot
        plt.show()
        
        # Save the plot as a PNG file with the key name
        fig.savefig(f"{key}.png")
        
        # Close the figure to free up memory
        plt.close(fig)