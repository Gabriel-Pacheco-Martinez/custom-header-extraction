import os
import json

def read_json(path):
    with open(path, "r") as f:
        return json.load(f)

def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        if isinstance(data, set):
            data = list(data)
        json.dump(data, f, indent=2)

def load_standard_headers(filename):
    with open(filename, "r", encoding="utf-8") as f:
        headers = {line.strip().lower() for line in f if line.strip()}
    return headers