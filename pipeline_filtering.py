import urllib
import os
from information_api import save_json

#####################################
# Pipeline
#####################################
def heuristics_filtering_pipeline(all_headers, known_standard_headers, stored_values, output_folder):
    # Initialize counts
    n_total_headers = 0
    n_final_headers = 0

    # Initialize header storage
    custom_headers = []
    standard_headers = {}
    seen_headers = {}

    # Compound filtering statistics
    compound_filtering_stats = {
        "standard_headers": 0,
        "third_party": 0,
        "min_length": 0,
        "inconsistent": 0,
        "not_in_storage": 0
    }

    # Flags to enable desired filters
    apply_pre_processing = True
    apply_heuristic_1 = True
    apply_heuristic_2 = True
    apply_heuristic_3 = True
    apply_heuristic_4 = True


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

        # === Heuristic 3: Consistent value
        if apply_heuristic_3:
            seen_headers, is_consistent = check_if_consistent_value(
                curr_header["header_name"], curr_header["header_value"], seen_headers)
            if not is_consistent:
                compound_filtering_stats["inconsistent"] += 1
                continue

        # === Heuristic 4: Stored in cookies/local
        if apply_heuristic_4:
            is_in_cookies_local = check_if_in_storage(curr_header["header_value"], stored_values)
            if not is_in_cookies_local:
                compound_filtering_stats["not_in_storage"] += 1
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

def check_if_consistent_value(name, value, seen_headers):
    if name in seen_headers:
        if seen_headers[name] != value:
            return seen_headers, 0
    else:
        seen_headers[name] = value
    return seen_headers, 1

def check_if_in_storage(value, set):
    if value in set:
        return 1
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
