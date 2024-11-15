from matplotlib import pyplot as plt
import pandas as pd
import networkx as nx
import multiprocessing as mp

from save_load_ledger import *
from graph_stats import *


def create_conflict_graph(block, additional_ops):
    txs = block["transactions"]
    # Initialize a graph
    G = nx.Graph()

    for tx in txs:
        G.add_node(tx['hash'])

    ops = additional_ops

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
                and (t1["op"] == "write" and t2["op"] == "write")
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
        "hash": block["hash"],
        "txs": len(block["transactions"]),
        "degree": graph_average_degree(conflict_graph),
        "colors": graph_coloring(conflict_graph),
        # "assortativity": graph_assortativity(conflict_graph),
        "cluster_coe": graph_cluster_coe(conflict_graph),
        "density": graph_density(conflict_graph),
        # "edge_con": graph_edge_connectivity(conflict_graph),
        "modularity": graph_modularity(conflict_graph),
        "transitivity": graph_transitivity(conflict_graph),
        "diameter": graph_diameter(conflict_graph)
    }
    return results

def main():
    '''
    receipts = []
    with open("recepit_209_to_210_next.pkl", "rb") as f:
        while True:
            try:
                receipt = pickle.load(f)
                receipts.append(receipt)
            except EOFError:
                break
    x = 3
    '''
    
    fetch_and_save_recepits()
    # return
    '''
    start = 20000000
    end = 20100000

    numbers_set = set()
    full_range = set(range(start, end))
    for block in load_ledger():
        block_number = block['number']
        numbers_set.add(block_number)
        print(block_number)
    
    missing_numbers = full_range - numbers_set
    print(sorted(missing_numbers))
    print(len(missing_numbers))

    # fetch_and_save_blocks()
    '''
    return

    i = 20000000
    with open("fixed.pkl", "ab") as ff:
        for block in load_ledger():
            block_number = block['number']
            print(block_number, i)
            for j in range(i, block_number):
                b = fetch_block(random.choice(eth_clients), j)
                i += 1
                pickle.dump(b, ff)
            if block_number == i:
                pickle.dump(block, ff)
            else:
                return
            i += 1
    return
    

    with open("recepit.pkl", "ab") as f:
        for block in load_ledger(2):
            additional_ops = []
            receipts = load_receipts(block['number'])
            for tx in block['transactions']:
                if is_smart_contract_interaction(tx):
                    tx_rs = [r for h,r in receipts if h == tx['hash']]
                    receipts_write_addresses = list([get_write_addresses(receipt) for receipt in tx_rs])
                    write_addresses = list(set(sum(receipts_write_addresses, [])))
                    read_addresses = estimate_read_addresses(tx, write_addresses)
                    additional_ops += [{"hash" :tx['hash'], "data": addr, "op": 'write'} for addr in write_addresses]
                    additional_ops += [{"hash" :tx['hash'], "data": addr, "op": 'read'} for addr in read_addresses]
                else:
                    continue
            G = create_conflict_graph(block, additional_ops)
            x = 3
            plt.figure(figsize=(8, 6))  # Set the figure size
            nx.draw(G)
            plt.show()
    return
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

        props = list([k for k in data[0].keys() if k != "txs" and k != "hash"])

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
        ax.set_scale('log')
        ax.grid(True)
        
        # Display the plot
        plt.show()
        
        # Save the plot as a PNG file with the key name
        fig.savefig(f"{key}.png")
        
        # Close the figure to free up memory
        plt.close(fig)


if __name__ == "__main__":
    main()