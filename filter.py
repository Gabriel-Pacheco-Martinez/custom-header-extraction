import os
import json
import tldextract
import parser
import urllib

#####################################
# Filtering pipeline
#####################################
def filter_headers(events, hostname, driver, output_folder):
    # Initialize variables
    n_total_headers = 0
    n_final_headers = 0
    custom_headers = []
    seen_headers = {}  # all
    standard_headers = {}  # only standard

    # Flags to enable desired filters
    apply_pre_processing = True
    apply_heuristic_1 = False
    apply_heuristic_2 = True
    apply_heuristic_3 = True
    apply_heuristic_4 = True

    # Heuristic filter-out counters
    filter_stats = {
        "third_party": 0,
        "min_length": 0,
        "inconsistent": 0,
        "not_in_storage": 0
    }

    # Get current hostname
    hostname_domain = get_domain(hostname)

    # Values stored in cookies/local
    cookies = driver.get_cookies()
    local_storage = driver.execute_script("return {...localStorage}")
    session_storage = driver.execute_script("return {...sessionStorage}")
    stored_values = set()  # Set to store values for cookies/local

    # Extract and parse values for cookies/local
    stored_values.update(parser.extract_all_cookie_values(cookies))
    stored_values.update(parser.extract_all_storage_session_values(local_storage))
    stored_values.update(parser.extract_all_storage_session_values(session_storage))

    # Get list of standard headers
    standard_headers_set = load_standard_headers("standard_headers.txt")

    for event in events:
        method = event.get("method")
        params = event.get("params")
        headers = None
        method_domain = None
        method_type = None

        if method == "Network.requestWillBeSent":
            request = params.get("request")
            request_url = request.get("url")
            method_domain = get_domain(request_url)
            headers = request.get("headers")
            method_type = "REQUEST"
        elif method == "Network.responseReceived":
            response = params.get("response")
            response_url = response.get("url")
            method_domain = get_domain(response_url)
            headers = response.get("headers")
            method_type = "RESPONSE"

        # Loop through all headers in current event
        for header_name, header_value in headers.items():
            n_total_headers += 1

            # === Preprocessing: Standard header check
            if apply_pre_processing:
                standard_headers, is_custom = check_if_custom_header(
                    header_name, standard_headers_set, standard_headers)
                if not is_custom:
                    continue

            # ===
            # Statistics
            filtering_stats_heuristic_1(filter_stats, "third_party", method_domain, hostname_domain)
            filtering_stats_heuristic_2(filter_stats, "min_length", header_value)
            filtering_stats_heuristic_3(filter_stats, "inconsistent", header_name, header_value, seen_headers)
            filtering_stats_heuristic_4(filter_stats, "not_in_storage", header_value, stored_values)

            # ====
            # Pipeline
            # === Heuristic 1: Third-party association
            if apply_heuristic_1:
                is_third_party = check_if_third_party_associated(method_domain,hostname_domain)
                if not is_third_party:
                    continue

            # === Heuristic 2: Minimum value length
            if apply_heuristic_2:
                is_min_val = check_if_min_value_length(header_value)
                if not is_min_val:
                    continue

            # === Heuristic 3: Consistent value
            if apply_heuristic_3:
                seen_headers, is_consistent = check_if_consistent_value(
                    header_name, header_value, seen_headers)
                if not is_consistent:
                    continue

            # === Heuristic 4: Stored in cookies/local
            if apply_heuristic_4:
                is_in_cookies_local = check_if_in_storage(header_value, stored_values)
                if not is_in_cookies_local:
                    continue

            # === Passed all
            n_final_headers += 1
            custom_headers.append({
                "method": method_type,
                "header_name": header_name,
                "header_value": header_value,
                "host_domain": hostname_domain,
                "method_domain": method_domain
            })

    # Output
    print("Total headers:", n_total_headers)
    print("Final headers:", n_final_headers)
    build_filter_report(filter_stats, n_total_headers, output_folder)

    # return custom_headers, stored_values
    return custom_headers, standard_headers, stored_values

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
# Helper Functions
#####################################
def get_domain(url):
    try:
        return tldextract.extract(url).top_domain_under_public_suffix
    except:
        return "invalid"

def load_standard_headers(filename):
    with open(filename, "r", encoding="utf-8") as f:
        headers = {line.strip().lower() for line in f if line.strip()}
    return headers

def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def build_filter_report(filter_stats, total_headers, output_folder):

    heuristic_names = {
        "third_party": "Third-party association",
        "min_length": "Mininum-Value Length",
        "inconsistent": "Consistent-Value",
        "not_in_storage": "Retreived C/S"
    }

    report = {"Headers retrieved post filtering": {}}

    for key, filtered_out in filter_stats.items():
        heuristic_name = heuristic_names.get(key, key)
        retrieved = total_headers - filtered_out
        report["Headers retrieved post filtering"][heuristic_name] = {
            "Total headers": total_headers,
            "Retrieved headers": retrieved
        }

    save_json(report, os.path.join(output_folder, "filter_stats.json"))

#####################################
# Filtering Stats
#####################################
def filtering_stats_heuristic_1(map, key, method, host):
    is_third_party = check_if_third_party_associated(method, host)
    if not is_third_party:
        map[key] += 1

def filtering_stats_heuristic_2(map, key, value):
    is_min_val = check_if_min_value_length(value)
    if not is_min_val:
        map[key] += 1

def filtering_stats_heuristic_3(map, key, name, value, seen_headers):
    seen_headers, is_consistent = check_if_consistent_value(
        name, value, seen_headers)
    if not is_consistent:
        map[key] += 1

def filtering_stats_heuristic_4(map, key, value, stored_values):
    is_in_cookies_local = check_if_in_storage(value, stored_values)
    if not is_in_cookies_local:
        map[key] += 1