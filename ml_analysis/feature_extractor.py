import json
import re
import os
import csv
import math
import base64
import binascii
from uuid import UUID
from urllib.parse import unquote
from collections import Counter, defaultdict

###############################
# Helper functions
###############################
def shannon_entropy_measure(s):
    if not s:
        return 0
    probs = [freq / len(s) for freq in Counter(s).values()]
    return -sum(p * math.log2(p) for p in probs)

def is_uuid(s):
    try:
        UUID(s)
        return True
    except ValueError:
        return False

def is_base64(s):
    try:
        s_clean = s.strip().replace("\n", "").replace(" ", "")

        # Add padding if missing
        missing_padding = len(s_clean) % 4
        if missing_padding:
            s_clean += "=" * (4 - missing_padding)

        decoded = base64.b64decode(s_clean, validate=True)

        # Optional: check if it's valid UTF-8 text
        try:
            decoded.decode('utf-8')
        except UnicodeDecodeError:
            pass  # still valid base64, just not UTF-8 text

        return True
    except (binascii.Error, ValueError):
        return False

def is_jwt(s):
    parts = s.split('.')
    return len(parts) == 3 and all(is_base64(part) for part in parts)


#########################
# Evaluate a single custom header
#########################
def individual_header_analysis(curr, host_domains, destination_domains):
    curr_name = curr.get("header_name", "")
    curr_value = unquote(str(curr.get("header_value", "")))

    return {
        # Header properties
        "method": curr.get("method"),
        "header_name": curr_name,
        "header_value": curr_value,

        # Counts
        "header_name_length": len(curr_name),
        "header_value_length": len(curr_value),
        "num_letters_in_value": sum(1 for c in curr_value if c.isalpha()),
        "num_numbers_in_value": sum(1 for c in curr_value if c.isdigit()),
        "num_special_chars_in_value": sum(1 for c in curr_value if not c.isalnum()),

        # Value characteristics
        "value_is_uuid": is_uuid(curr_value),
        "value_is_base64": is_base64(curr_value),
        "value_is_jwt": is_jwt(curr_value),

        # Entropy analysis
        # "header_name_entropy": shannon_entropy_measure(curr_name),
        # "header_value_entropy": shannon_entropy_measure(curr_value),

        # Consistency and storage
        "consistency_across_visits": "TRUE",
        "stored_in_cookies_or_local": "TRUE",

        # Host and Destination diversity
        "host_domains":  host_domains.get((curr_name, curr_value), "N/A"),
        "destination_domains": destination_domains.get((curr_name, curr_value), "N/A")
    }

# =====================
# Main
# =====================
def perform_feature_extraction():
    # Print information
    print("\n=================")
    print("FEATURE EXTRACTION:")
    print("=================")

    json_file_path = r"log_collect_filter/results/all_custom_headers.json"
    csv_file = "ml_analysis/csv_files_before_models/tracking_headers.csv"
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)

    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # =======
    # Step 1: Build (header_name, header_value) → set of host domains
    header_to_hosts = defaultdict(set)
    header_to_destinations = defaultdict(set)
    for group in data:
        for header in group:
            name = header.get("header_name", "")
            value = unquote(str(header.get("header_value", "")))
            host = header.get("host_domain", "")
            destination = header.get("method_domain", "")
            header_to_hosts[(name, value)].add(host)
            header_to_destinations[(name,value)].add(destination)

    # =======
    # Step 2: Keep only unique (name, value) pairs for CSV
    seen_pairs = set()
    rows_for_csv = []
    for group in data:
        for header in group:
            name = header.get("header_name", "")
            value = unquote(str(header.get("header_value", "")))
            key = (name, value)

            if key in seen_pairs:
                continue  # skip duplicate

            seen_pairs.add(key)
            features_extracted = individual_header_analysis(header, header_to_hosts, header_to_destinations)
            rows_for_csv.append(features_extracted)

    # =======
    # Step 3: Write to CSV
    if rows_for_csv:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows_for_csv[0].keys()))
            writer.writeheader()
            writer.writerows(rows_for_csv)
        print(f"✅ CSV for ML analysis created with {len(rows_for_csv)} unique headers")
    else:
        fieldnames = [
            "method", "header_name", "header_value",
            "header_name_length", "header_value_length",
            "num_letters_in_value", "num_numbers_in_value", "num_special_chars_in_value",
            "value_is_uuid", "value_is_base64", "value_is_jwt",
            "header_name_entropy", "header_value_entropy",
            "host_domains", "destination_domains"
        ]
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        print("⚠️ Extractor: No headers found to write.")

if __name__ == "__main__":
    perform_feature_extraction()