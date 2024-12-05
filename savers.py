import os
import pickle

def save_to_file(file_path: str, generator, append_mode = False) -> None:
  if os.path.exists(file_path) and not append_mode:
    raise Exception(f"{file_path} already exists!")
  with open(file_path, "ab") as f:
    for i, entry in enumerate(generator):
      print(f"Saved entry {i} to {file_path}")
      pickle.dump(entry, f)