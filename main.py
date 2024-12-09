import csv
from itertools import islice
import json
import os
import pickle
import h5py
from matplotlib import pyplot as plt
import pandas as pd
import networkx as nx
import multiprocessing as mp

from fetchers import fetch_parallel, fetcher_prestate
from parsers import create_conflict_graph, parse_callTracer_trace, parse_preStateTracer_trace
from graph_stats import *

from plotters import plot_data
from savers import append_to_file, save_prestate, save_to_file

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from loaders import load_compressed_file, load_file

def process_prestate_trace(block_number, diffFalse, diffTrue):
    print(f"processing {block_number}...")
    if diffFalse is None or diffTrue is None:
        print(f"{block_number} data is missing!")
        return None
    reads, writes = parse_preStateTracer_trace(diffFalse, diffTrue)
    txs = [tx_trace["txHash"] for tx_trace in diffFalse]
    G = create_conflict_graph(txs, reads, writes)
    return get_graph_stats(G, {"block_number": block_number, "txs": len(diffFalse)})

def process_call_trace(block_number, call_trace):
    print(f"processing {block_number}...")
    if call_trace is None:
        print(f"{block_number} data is missing!")
        return None
    reads, writes = parse_callTracer_trace(call_trace)
    txs = [tx_trace["txHash"] for tx_trace in call_trace]
    G = create_conflict_graph(txs, reads, writes)
    return get_graph_stats(G, {"block_number": block_number, "txs": len(call_trace)})

def generate_data(data_path, output_path, processor, limit = None):
    write_header = not os.path.exists(output_path)
    max_pending = 1000
    with open(output_path, mode="a", newline="") as file:
        with ProcessPoolExecutor() as pool:
            data_generator = load_compressed_file(data_path, limit)
            futures = [
                pool.submit(processor, *data) for data in islice(data_generator, max_pending)
            ]
            all_submitted = len(futures) < max_pending
            writer = csv.writer(file)
            i = 0
            while len(futures) > 0:
                future = futures[0]
                futures = futures[1:]
                result = future.result()
                if result is not None:
                    if write_header:
                        write_header = False
                        writer.writerow(result.keys())
                    writer.writerow(result.values())
                    print(f"wrote result {i} to output csv")
                    i += 1
                if not all_submitted:
                    try:
                        next_data = next(data_generator)
                        futures.append(pool.submit(processor, *next_data))
                    except StopIteration:
                        all_submitted = True

def get_files(folder_path, extension):
    return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(extension)]

def main():
    dirpath = f"F:\\prev_E\\traces"
    output_path = "output.csv"
    if os.path.exists(output_path):
        os.remove(output_path)
    for file in get_files(dirpath, ".h5"):
        generate_data(file, "output.csv")
    plot_data(output_path)

def download():
    dirpath = f"F:\\prev_E\\traces"
    filesize = 1000
    for begin in range(21021000, 21100000, filesize):
        end = begin + filesize
        filename = f"{begin}_{end}_preState_compressed.h5"
        traces_generator = fetch_parallel(begin, end, fetcher_prestate)
        save_to_file(os.path.join(dirpath, filename), traces_generator)

def generator_old(filepath):
    with open(filepath, "rb") as f:
        for i in range(100000000000000000):
            try:
                result = pickle.load(f)
                print(f"loaded {i}")
                yield result
            except:
                break   

def translate(path_src, path_dst):
    save_to_file(path_dst, generator_old(path_src))

if __name__ == "__main__":
    for filepath in get_files("E:\\eth_traces\\callTracer", "h5"):
        generate_data(filepath, "output_calltracer.csv", process_call_trace)
    plot_data('output_calltracer.csv')