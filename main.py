from matplotlib import pyplot as plt
import pandas as pd
import networkx as nx
import multiprocessing as mp

from parsers import create_conflict_graph, parse_callTracer_trace, parse_preStateTracer_trace
from save_load_ledger import *
from graph_stats import *




import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from loaders import load_file

def process_prestate_trace(block_number, traces):
    trace_diffTrue, trace_diffFalse = traces
    return None

def generate_data(data_path, limit = None):
    data = []
    with mp.Pool() as pool:
        async_results = []
        for block_number, block_trace in load_file(data_path, limit):
            async_result = pool.apply_async(process_prestate_trace, (block_number, block_trace,))
            async_results.append(async_result)
        for i, async_result in enumerate(async_results):
            result = async_result.get()
            data.append(result)
            print(i)
        df = pd.DataFrame(data)
        df.to_csv("data.csv", index=False)

def main():
    pass

if __name__ == "__main__":
    main()
        