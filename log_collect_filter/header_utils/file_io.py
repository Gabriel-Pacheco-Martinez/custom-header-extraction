import os
import json
import re

def read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Remove problematic control characters
        content = re.sub(r'[\x00-\x1f]', '', content)

        return json.loads(content)
    except Exception as e:
        print(f"⚠️ Failed to read JSON: {e}")
        return None

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