import json
import os
import h5py

from fetchers import fetcher_prestate, fetch_parallel

def save_prestate(filename: str, range_start: int, range_stop: int):
  generator = fetch_parallel(range_start, range_stop, fetcher_prestate)
  save_to_file(filename, generator, range_stop-range_start)
    

def save_to_file(filename: str, generator, total_size) -> None:
  if os.path.exists(filename):
    raise Exception(f"{filename} already exists!")
  with h5py.File(filename, 'w') as f:
      chunk_size = min(256, total_size)
      dset = f.create_dataset(
          'dataset',
          shape=(total_size,),
          dtype=h5py.string_dtype(encoding='ascii'),
          chunks=(chunk_size,),
          compression='gzip',
          compression_opts=9
      )

      for i in range(0, total_size, chunk_size):
          start = i
          end = min(i + chunk_size, total_size)
          chunk = [json.dumps(value) for i, value in enumerate(generator) if i < chunk_size]
          dset[start:end] = chunk
          print(f"saved {i} values")