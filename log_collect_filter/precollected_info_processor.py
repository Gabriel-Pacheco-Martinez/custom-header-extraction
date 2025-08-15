# General
import os
import urllib.parse
import tldextract
from urllib.parse import urlparse

# Mine
from log_collect_filter.header_utils.file_io import read_json, save_json, load_standard_headers


# =======
# Helper functions
# =======
def check_if_header_is_custom(name, _default_headers):
    name = name.lower() # ensure all in lower case

    # Return false if the header is not custom (found in standard headers list)
    if name in _default_headers:
        return False
    return True

def check_if_third_party(_host_domain, _method_domain):
    return _host_domain != _method_domain

def check_if_min_value_length(value):
    return len(urllib.parse.unquote(value)) >= 8

def check_if_url(value):
    try:
        result = urlparse(value)
        return 1 if result.scheme in ("http", "https") and result.netloc else 0
    except:
        return 0

def get_domain(url):
    try:
        return tldextract.extract(url).top_domain_under_public_suffix
    except:
        return "invalid"

# =======
# MAIN
# =======
def perform_external_data_processing():
    tot_headers = 0
    tot_tracking_headers = 0

    # =======
    # Variable to store tracking headers
    tracking_headers = []

    # =======
    # Set capture folder
    capture_folder = os.path.join("log_collect_filter", "results")
    os.makedirs(capture_folder, exist_ok=True)

    # =======
    # Read required files
    try:
        all_headers = read_json("data/custom_header_value.json")
        # print("✅ Found. Contents of custom_header_value.json:")
        # print(all_headers)
    except FileNotFoundError:
        print("⚠️ File not found: 'custom_header_value.json'")
        return

    try:
        default_headers = load_standard_headers("std_headers/standard_headers.txt")
        # print("✅ Found. Contents of standard_headers.txt:")
        # print(default_headers)
    except FileNotFoundError:
        print("⚠️ File not found: 'standard_headers.txt'")
        return

    # Filtering stats
    filtering_stats = {
        # Original heuristics
        "standard_headers": 0,
        "third_party": 0,
        "min_length": 0,
        "url": 0
    }

    # Flags to enable desired filters
    apply_pre_processing = True  # std_headers
    apply_heuristic_1 = True  # third party
    apply_heuristic_2 = True  # min length
    apply_heuristic_3 = True  # url

    for map_key, map_value in all_headers.items():
        key_str_1, key_str_2 = map_key.split("|", 1) # Because of schema "key|value1,value2"

        # Skip if header has more than one value (means it has no consistency)
        components  = [v.strip() for v in key_str_2.split(",")]
        if len(components)>1:
            continue

        # Define header name and value
        header_name = key_str_1
        header_value = components[0]

        # Loop over all instances found for key|value pair
        instances = map_value[7]

        for instance in instances:
            method = "REQUEST" if instance[1] == "req" else "RESPONSE"
            host_domain = instance[2]
            method_domain =  get_domain(instance[0])

            tot_headers += 1

            # ====
            # Pipeline
            # ==== Preprocessing: Standard header check
            if apply_pre_processing:
                is_custom = check_if_header_is_custom(header_name, default_headers)
                if not is_custom:
                    filtering_stats["standard_headers"] += 1
                    continue

            # === Heuristic 1: Third-party association
            if apply_heuristic_1:
                is_third_party = check_if_third_party(host_domain, method_domain)
                if not is_third_party:
                    filtering_stats["third_party"] += 1
                    continue

            # === Heuristic 2: Minimum value length
            if apply_heuristic_2:
                is_min_val = check_if_min_value_length(header_value)
                if not is_min_val:
                    filtering_stats["min_length"] += 1
                    continue

            # === Heuristic 3: Check if its url
            if apply_heuristic_3:
                is_url = check_if_url(header_value)
                if is_url:
                    filtering_stats["url"] += 1
                    continue

            # === Passed filters
            tot_tracking_headers += 1
            try:
                tracking_headers.append({
                    "method": method,
                    "header_name": header_name,
                    "header_value": header_value,
                    "host_domain": host_domain,
                    "method_domain": method_domain
                })
            except Exception as e:
                print(f"Failed to append header due to: {e}")

    # =======
    # Save json with tracking headers
    save_json(tracking_headers, os.path.join(capture_folder, "all_custom_headers.json"))

    # =======
    # Print information
    print("\n=================")
    print("PROCESS SUMMARY:")
    print("=================")
    print("total custom headers into filter: ", tot_headers)
    print("total tracking custom headers: ", tot_tracking_headers)
    print("===")
    print("filtered for standard headers:", filtering_stats["standard_headers"])
    print("filtered for first party:", filtering_stats["third_party"])
    print("filtered for minimum length:", filtering_stats["min_length"])
    print("filtered for being url:", filtering_stats["url"])

if __name__ == "__main__":
    perform_external_data_processing()