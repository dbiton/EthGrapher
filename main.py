import json
import h5py
from matplotlib import pyplot as plt
import pandas as pd
import networkx as nx
import multiprocessing as mp

from parsers import create_conflict_graph, parse_callTracer_trace, parse_preStateTracer_trace
from graph_stats import *

from plotters import plot_data
from savers import save_prestate


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from loaders import load_file

def process_prestate_trace(block_number, diffFalse, diffTrue):
    print(f"processing {block_number}...")
    reads, writes = parse_preStateTracer_trace(diffFalse, diffTrue)
    G = create_conflict_graph(reads, writes)
    return get_graph_stats(G, {"block_number": block_number, "txs": len(diffFalse)})

def generate_data(data_path, limit = None):
    data = []
    with mp.Pool() as pool:
        async_results = []
        for block_number, diffFalse, diffTrue in load_file(data_path):
            async_result = pool.apply_async(process_prestate_trace, (block_number, diffFalse, diffTrue))
            async_results.append(async_result)
        for i, async_result in enumerate(async_results):
            result = async_result.get()
            data.append(result)
        df = pd.DataFrame(data)
        df.to_csv("data.csv", index=False)

def main():
    # save_prestate("21000000_preState.h5", 21000000, 21000100)
    generate_data("21000000_preState.h5")
    plot_data("data.csv")

if __name__ == "__main__":
    main()