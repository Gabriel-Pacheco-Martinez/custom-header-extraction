import urllib
import os
import math
from .file_io import save_json
from collections import Counter
from urllib.parse import urlparse
from collections import defaultdict


#####################################
# Pipeline
#####################################
def filter_pipeline(all_headers, all_headers_1, all_headers_2, known_standard_headers, storage_values, output_folder):
    # Initialize counts
    n_total_headers = len(all_headers)
    n_final_headers = 0

    # Initialize header storage
    custom_headers = []
    standard_headers = {}
    pipeline_headers = []

    # Compound filtering statistics
    compound_filtering_stats = {
        # Pre-processing
        "standard_headers": 0,

        # Original heuristics
        "third_party": 0,
        "min_length": 0,
        "inconsistent": 0,
        "not_in_storage": 0,
    }

    # Flags to enable desired filters
    apply_pre_processing = True     # std_headers
    apply_heuristic_1 = True        # third party
    apply_heuristic_2 = True       # min length, url, entropy
    apply_heuristic_3 = True      # inconsistent across session & across visits
    apply_heuristic_4 = True       # cookies/storage

    # Reference
    unique_after_preprocessing = 0
    unique_after_heuristic1 = 0
    unique_after_heuristic2 = 0
    unique_after_heuristic3 = 0
    unique_after_heuristic4 = 0

    # ====
    # Pipeline
    # ==== Preprocessing:
    if apply_pre_processing:
        pipeline_headers, standard_headers, = check_if_custom_header(all_headers, known_standard_headers)

        # Check values
        unique_after_preprocessing = len(set(h["header_name"] for h in pipeline_headers))
        filtered = n_total_headers - unique_after_preprocessing
        compound_filtering_stats["standard_headers"] = filtered

    # ==== Third-party association
    if apply_heuristic_1:
        pipeline_headers = check_if_third_party_associated(pipeline_headers)

        # Check values
        unique_after_heuristic1 = len(set(h["header_name"] for h in pipeline_headers))
        filtered = unique_after_preprocessing - unique_after_heuristic1
        compound_filtering_stats["third_party"] = filtered

    # === Heuristic 2: Minimum value length
    if apply_heuristic_2:
        pipeline_headers = check_if_min_value_length(pipeline_headers)

        # Check entropy of the value
        pipeline_headers = check_if_high_entropy(pipeline_headers)

        # Check if it's a url
        pipeline_headers = check_if_url(pipeline_headers)

        # Check values
        unique_after_heuristic2 = len(set(h["header_name"] for h in pipeline_headers))
        filtered = unique_after_heuristic1 - unique_after_heuristic2
        compound_filtering_stats["min_length"] = filtered

    # === Heuristic 3: Consistent value in visit
    if apply_heuristic_3:
        pipeline_headers = check_if_consistent_in_session(pipeline_headers, all_headers_1)

        # Consistent value across visits
        pipeline_headers = check_if_consistent_in_visits(pipeline_headers, all_headers_2)

        # Check values
        unique_after_heuristic3 = len(set(h["header_name"] for h in pipeline_headers))
        filtered = unique_after_heuristic2 - unique_after_heuristic3
        compound_filtering_stats["inconsistent"] = filtered

    # === Heuristic 4: Stored in cookies/local
    if apply_heuristic_4:
        pipeline_headers = check_if_in_storage(pipeline_headers, storage_values)

        # Check values
        unique_after_heuristic4 = len(set(h["header_name"] for h in pipeline_headers))
        filtered = unique_after_heuristic3 - unique_after_heuristic4
        compound_filtering_stats["not_in_storage"] = filtered


    # Output
    # print("Total headers:", n_total_headers)
    # print("Tracking headers:", n_final_headers)
    build_compound_filtering_report(compound_filtering_stats, n_total_headers, output_folder)

    return pipeline_headers, standard_headers

#####################################
# Heuristics/Filters
#####################################
def check_if_custom_header(headers, set_standard_headers):
    temp_headers = []
    seen_standard_headers = {}
    filtered_count = 0
    total = 0

    for curr_header in headers:
        total += 1

        # Function
        key = curr_header["header_name"].lower()

        if key in set_standard_headers:
            filtered_count += 1
            if key in seen_standard_headers:
                seen_standard_headers[key] += 1
            else:
                seen_standard_headers[key] = 1

        else:
            fields = ["method", "header_name", "header_value", "host_domain", "method_domain"]
            temp_headers.append({k: curr_header[k] for k in fields})

    return temp_headers, seen_standard_headers

def check_if_third_party_associated(headers):
    temp_headers = []
    filtered_count = 0

    for curr_header in headers:
        url = curr_header["method_domain"]
        hostname = curr_header["host_domain"]

        if url == hostname:
            filtered_count += 1
        else:
            fields = ["method", "header_name", "header_value", "host_domain", "method_domain"]
            temp_headers.append({k: curr_header[k] for k in fields})

    return temp_headers #returns true if they are different

def check_if_min_value_length(headers):
    temp_headers = []
    filtered_count = 0

    for curr_header in headers:
        value = curr_header["header_value"]

        if len(urllib.parse.unquote(value)) >= 7:
            fields = ["method", "header_name", "header_value", "host_domain", "method_domain"]
            temp_headers.append({k: curr_header[k] for k in fields})
        else:
            filtered_count += 1

    return temp_headers

def check_if_consistent_in_session(headers, all_headers_1):
    temp_headers = []
    filtered_count = 0

    for curr_header in headers:
        name = curr_header["header_name"]

        if name in all_headers_1:
            values = all_headers_1[name]
            ans = all(v == values[0] for v in values)

            if not ans:
                filtered_count += 1
            else:
                fields = ["method", "header_name", "header_value", "host_domain", "method_domain"]
                temp_headers.append({k: curr_header[k] for k in fields})

    return temp_headers

def check_if_consistent_in_visits(headers, all_headers_2):
    temp_headers = []
    filtered_count = 0

    for curr_header in headers:
        name = curr_header["header_name"]
        value = curr_header["header_value"]

        # Check if value consistent across visits
        if name in all_headers_2:
            v = all_headers_2[name][0]
            if not v == value:
                filtered_count += 1
            else:
                fields = ["method", "header_name", "header_value", "host_domain", "method_domain"]
                temp_headers.append({k: curr_header[k] for k in fields})

    return temp_headers

def check_if_in_storage(headers, set):
    temp_headers = []
    filtered_count = 0

    for curr_header in headers:
        value = curr_header["header_value"]
        if value not in set:
            filtered_count += 1
        else:
            fields = ["method", "header_name", "header_value", "host_domain", "method_domain"]
            temp_headers.append({k: curr_header[k] for k in fields})

    return temp_headers

def check_if_high_entropy(headers):
    temp_headers = []
    filtered_count = 0

    for curr_header in headers:
        value = curr_header["header_value"]

        probs = [freq / len(value) for freq in Counter(value).values()]
        entropy = -sum(p * math.log2(p) for p in probs)
        if entropy > 3:
            fields = ["method", "header_name", "header_value", "host_domain", "method_domain"]
            temp_headers.append({k: curr_header[k] for k in fields})
        else:
            filtered_count += 1

    return temp_headers

def check_if_url(headers):
    temp_headers = []
    filtered_count = 0
    common_extensions = (".com", ".org", ".net", ".edu", ".gov", ".io", ".co", ".us")

    for curr_header in headers:
        value = curr_header["header_value"].strip().lower()

        # Quick pattern check for www or common TLDs
        if value.startswith("www.") or value.endswith(common_extensions):
            filtered_count += 1
            continue  # ✅ skip saving, it's URL-like

        result = urlparse(value)

        if result.scheme in ("http", "https") and result.netloc:
            filtered_count += 1  # ✅ valid URL, filter it out
        else:
            # Not a URL → keep it
            fields = ["method", "header_name", "header_value", "host_domain", "method_domain"]
            temp_headers.append({k: curr_header[k] for k in fields})

    return temp_headers

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

