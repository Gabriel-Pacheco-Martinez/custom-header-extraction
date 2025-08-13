import urllib
import os
import math
from .file_io import save_json
from collections import Counter
from urllib.parse import urlparse


#####################################
# Pipeline
#####################################
def filter_pipeline(all_headers, all_headers_1, all_headers_2, known_standard_headers, storage_values, output_folder):
    # Initialize counts
    n_total_headers = 0
    n_final_headers = 0

    # Initialize header storage
    custom_headers = []
    standard_headers = {}
    seen_headers = {}

    # Compound filtering statistics
    compound_filtering_stats = {
        # Original heuristics
        "standard_headers": 0,
        "third_party": 0,
        "min_length": 0,
        "inconsistent_session": 0,
        "not_in_storage": 0,

        # Added heuristics
        "inconsistent_visits": 0,
        "low_entropy": 0,
        "contains_url": 0
    }

    # Flags to enable desired filters
    apply_pre_processing = True     # std_headers
    apply_heuristic_1 = True        # third party
    apply_heuristic_2 = True       # min length
    apply_heuristic_3 = True       # inconsistent across session
    apply_heuristic_4 = True       # cookies/storage
    apply_heuristic_5 = True       # inconsistent across visits

    apply_heuristic_6 = False       # has low entropy
    apply_heuristic_7 = False     # the value is an url


    for curr_header in all_headers:
        n_total_headers += 1

        # ====
        # Pipeline
        # ==== Preprocessing: Standard header check
        if apply_pre_processing:
            standard_headers, is_custom = check_if_custom_header(
                curr_header["header_name"], known_standard_headers, standard_headers)
            if not is_custom:
                compound_filtering_stats["standard_headers"] += 1
                continue

        # === Heuristic 1: Third-party association
        if apply_heuristic_1:
            is_third_party = check_if_third_party_associated(
                curr_header["method_domain"], curr_header["host_domain"])
            if not is_third_party:
                compound_filtering_stats["third_party"] += 1
                continue

        # === Heuristic 2: Minimum value length
        if apply_heuristic_2:
            is_min_val = check_if_min_value_length(
                curr_header["header_value"])
            if not is_min_val:
                compound_filtering_stats["min_length"] += 1
                continue

        # === Heuristic 3: Consistent value in visit
        if apply_heuristic_3:
            is_consistent_session = check_if_consistent_in_session(curr_header["header_name"], all_headers_1)
            if not is_consistent_session:
                compound_filtering_stats["inconsistent_session"] += 1
                continue

        # === Heuristic 4: Stored in cookies/local
        if apply_heuristic_4:
            is_in_cookies_local = check_if_in_storage(curr_header["header_value"], storage_values)
            if not is_in_cookies_local:
                compound_filtering_stats["not_in_storage"] += 1
                continue

        # === Heuristic 5: Consistent value across visits
        if apply_heuristic_5:
            is_consistent_visits = check_if_consistent_in_visits(
                curr_header["header_name"], curr_header["header_value"], all_headers_2)
            if not is_consistent_visits:
                compound_filtering_stats["inconsistent_visits"] = + 1
                continue

        # === Heuristic 6: Check entropy of the value
        if apply_heuristic_6:
            is_high_entropy = check_if_high_entropy(curr_header["header_value"])
            if not is_high_entropy:
                compound_filtering_stats["low_entropy"] += 1
                continue

        # === Heuristic 7: Check if it's a url
        if apply_heuristic_7:
            is_url = check_if_url(curr_header["header_value"])
            if is_url:
                compound_filtering_stats["contains_url"] += 1
                continue

        # === Passed filters
        n_final_headers += 1
        try:
            custom_headers.append({
                "method": curr_header["method"],
                "header_name": curr_header["header_name"],
                "header_value": curr_header["header_value"],
                "host_domain": curr_header["host_domain"],
                "method_domain": curr_header["method_domain"]
            })
        except Exception as e:
            print(f"Failed to append header due to: {e}")

    # Output
    print("Total headers:", n_total_headers)
    print("Final headers:", n_final_headers)
    build_compound_filtering_report(compound_filtering_stats, n_total_headers, output_folder)

    return custom_headers, standard_headers

#####################################
# Heuristics/Filters
#####################################
def check_if_custom_header(name, set_standard_headers, seen_standard_headers):
    key = name.lower()

    # The header is a standard header
    if key in set_standard_headers:
        if key in seen_standard_headers:
            seen_standard_headers[key] += 1
        else:
            seen_standard_headers[key] = 1
        return seen_standard_headers, 0

    # The header is a custom header
    return seen_standard_headers, 1

def check_if_third_party_associated(url, hostname):
    return url != hostname #returns true if they are different

def check_if_min_value_length(value):
    return len(urllib.parse.unquote(value)) >= 8 #returns true if length is bigger than 8

def check_if_consistent_in_session(name, all_headers_1):
    # Check if value consistent across current visit
    if name in all_headers_1:
        values = all_headers_1[name]
        ans = all(v == values[0] for v in values)
        return 0 if not ans else 1

    return 0

def check_if_consistent_in_visits(name, value, all_headers_2):
    # Check if value consistent across visits
    if name in all_headers_2:
        print(name)
        v = all_headers_2[name][0]
        print("v:",v)
        print("value:",value)
        return 0 if not v==value else 1

    # Consistent across visits
    return 1

def check_if_in_storage(value, set):
    if value not in set:
        return 0
    return 1

def check_if_high_entropy(value):
    probs = [freq / len(value) for freq in Counter(value).values()]
    entropy = -sum(p * math.log2(p) for p in probs)
    if entropy<3:
        return 0
    return 1

def check_if_url(value):
    try:
        result = urlparse(value)
        return 1 if result.scheme in ("http", "https") and result.netloc else 0
    except:
        return 0

#####################################
# Report
#####################################
def build_compound_filtering_report(stats, total_headers, output_folder):
    report = {"Compound filtering statistics": {}}
    for key, value in stats.items():
        report["Compound filtering statistics"][key] = {
            "Headers into filter": total_headers,
            "Headers removed": value
        }
        total_headers = total_headers-value

    save_json(report, os.path.join(output_folder, "compound_filter_stats.json"))
