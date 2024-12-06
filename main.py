import csv
import json
import os
import h5py
from matplotlib import pyplot as plt
import pandas as pd
import networkx as nx
import multiprocessing as mp

from fetchers import fetch_parallel, fetcher_prestate
from parsers import create_conflict_graph, parse_callTracer_trace, parse_preStateTracer_trace
from graph_stats import *

from plotters import plot_data
from savers import save_prestate, save_to_file

from concurrent.futures import ProcessPoolExecutor

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from loaders import load_compressed_file, load_file

def process_prestate_trace(block_number, diffFalse, diffTrue):
    print(f"processing {block_number}...")
    reads, writes = parse_preStateTracer_trace(diffFalse, diffTrue)
    G = create_conflict_graph(reads, writes)
    return get_graph_stats(G, {"block_number": block_number, "txs": len(diffFalse)})

def generate_data(data_path, output_path, limit = None):
    write_header = not os.path.exists(output_path)
    with open(output_path, mode="a", newline="") as file:
        with ProcessPoolExecutor(4) as pool:
            futures = [
                pool.submit(process_prestate_trace, block_number, diffFalse, diffTrue) 
                for block_number, diffFalse, diffTrue in load_compressed_file(data_path, limit)
            ]
            writer = csv.writer(file)
            for i, future in enumerate(futures):
                result = future.result()
                if write_header:
                    write_header = False
                    writer.writerow(result.keys())
                writer.writerow(result.values())
                print(f"wrote result {i} to output csv")

def get_files(folder_path, extension):
    return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(extension)]

def main():
    dirpath = f"F:\\prev_E\\traces"
    output_path = "output.csv"
    if os.path.exists(output_path):
        os.remove(output_path)
    for file in get_files(dirpath, ".h5"):
        generate_data(file, "output.csv")
    plot_data()
    
if __name__ == "__main__":
    main()
