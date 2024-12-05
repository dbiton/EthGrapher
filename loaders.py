from itertools import count
import os
import pickle


def load_file(filepath: str, limit=None):
    limit_range = count()
    if limit is not None:
      limit_range = range(limit)
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            for i in limit_range:
                try:
                  data = pickle.load(f)
                  print(f"Loaded entry {i} from {filepath}")
                  yield data
                except EOFError:
                    return
    else:
        print("No traces file found.")