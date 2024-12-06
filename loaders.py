import json
import os
import pickle
import zlib

import h5py

from parsers import apply_recursively, bytes_to_hex


def load_compressed_file(filepath: str, limit=None):
    if os.path.exists(filepath):
        with h5py.File(filepath, 'r') as f:
            dset = f['dataset']
            i = 0
            for i_chunk in range(dset.shape[0]):
                chunk = bytes(dset[i_chunk])
                chunk = zlib.decompress(chunk)
                chunk = pickle.loads(chunk)   
                for value in chunk:
                    i += 1
                    print(f"loaded {i} values from {filepath}")
                    yield apply_recursively(value, bytes_to_hex)
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