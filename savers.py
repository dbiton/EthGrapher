import json
import math
import os
import pickle
import h5py
import zlib
import numpy as np

from fetchers import fetcher_prestate, fetch_parallel
from parsers import apply_recursively, hex_to_bytes

def save_prestate(filename: str, range_start: int, range_stop: int):
  generator = fetch_parallel(range_start, range_stop, fetcher_prestate)
  save_to_file(filename, generator, range_stop-range_start)
    

def save_to_file(filename: str, generator, total_size) -> None:
  if os.path.exists(filename):
    raise Exception(f"{filename} already exists!")
  with h5py.File(filename, 'w') as f:
      chunk_size = min(128, total_size)
      chunk_count = int(math.ceil(total_size/chunk_size))
      dset = f.create_dataset(
          'dataset',
          shape=(chunk_count,),
          dtype=h5py.vlen_dtype(np.dtype('uint8')),
      )
      for i in range(0, total_size, chunk_size):
          start = i
          end = min(i + chunk_size, total_size)
          i_chunk = i // chunk_size
          chunk = [next(generator) for _ in range(start, end)]
          chunk = json.dumps(chunk)
          chunk = chunk.encode('ascii')
          chunk = zlib.compress(chunk, 3)
          chunk = np.frombuffer(chunk, dtype=np.uint8)
          dset[i_chunk] = chunk
          print(f"Saved {end} values in total to {filename}")