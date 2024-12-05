import json
import os
import h5py

def save_to_file(filename: str, generator, total_size) -> None:
  if os.path.exists(filename):
    raise Exception(f"{filename} already exists!")
  with h5py.File(filename, 'w') as f:
      chunk_size = 256
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
          chunk = [json.dump(value) for value in generator]
          dset[start:end] = chunk