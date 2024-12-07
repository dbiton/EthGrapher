import json
import os
import pickle
import zlib

import h5py

from parsers import apply_recursively, bytes_to_hex
from concurrent.futures import ThreadPoolExecutor

def uncompress_chunk(dset, i):
    chunk = dset[i]
    if len(chunk) == 0:
        return []
    chunk = bytes(chunk)
    chunk = zlib.decompress(chunk)
    chunk = chunk.decode('ascii')
    chunk = json.loads(chunk)
    return chunk

def load_compressed_file(filepath: str, limit=None):
    if os.path.exists(filepath):
        with h5py.File(filepath, 'r') as f:
            dset = f['dataset']
            i = 0
            with ThreadPoolExecutor() as pool:
                futures = [
                    pool.submit(uncompress_chunk, dset, i_chunk) 
                    for i_chunk in range(dset.shape[0])
                ]
                for future in futures:
                    entries = future.result()
                    for entry in entries:
                        i += 1
                        print(f"loaded {i} values from {filepath}")
                        yield entry
                        if i == limit:
                            return
    else:
        print("No traces file found.")

def load_file(filepath: str, limit=None):
    if os.path.exists(filepath):
        with h5py.File(filepath, 'r') as f:
            dset = f['dataset']
            limit = limit if limit is not None else dset.shape[0]
            for i in range(limit):
                value = json.loads(dset[i])
                yield value  # Read one line at a time
    else:
        print("No traces file found.")