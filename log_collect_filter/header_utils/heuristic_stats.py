import itertools
import urllib.parse
import math
from .file_io import save_json
from collections import Counter
from urllib.parse import urlparse

#####################################
# Permutations
#####################################
def filter_combinations(all_headers, all_headers_1, all_headers_2, known_standard_headers, storage_values, output_folder):
    filters = [
        third_party, min_length, consistent_session, not_in_storage, consistent_visits, entropy, url
    ]
    n=1

    for r in range(1, len(filters)+1):
        for combo in itertools.combinations(filters,r):
            filtering_stats = {
                "third_party": 0,
                "min_length": 0,
                "inconsistent_session": 0,
                "not_in_storage": 0,
                "inconsistent_visits": 0,
                "entropy": 0,
                "contains_url": 0
            }
            seen_headers = {}
            surviving_headers = []

            for header in all_headers:
                passed = True

                for curr_func in combo:
                    if not curr_func(header, all_headers_1, all_headers_2, seen_headers, storage_values, filtering_stats):
                        passed = False
                        break

                if passed:
                    surviving_headers.append(header)

            output_file = output_folder + "/filtering_combination" + str(n) + ".json"
            combo_label = f"Combination {n}: " + " + ".join(f.__name__ for f in combo)

            build_combination_report(
                filtering_stats, len(all_headers), output_file, combo_label
            )
            n += 1

#####################################
# Heuristics/Filters
#####################################
def third_party(header, all_headers_1, all_headers_2, seen_headers, storage_values, filtering_stats):
    if header["host_domain"] == header["method_domain"]:
        filtering_stats["third_party"] += 1
        return False
    return True

def min_length(header, all_headers_1, all_headers_2, seen_headers, storage_values, filtering_stats):
    if len(urllib.parse.unquote(header["header_value"])) >= 8:
        filtering_stats["min_length"] += 1
        return False
    return True

def consistent_session(header, all_headers_1, all_headers_2, seen_headers, storage_values, filtering_stats):
    name = header["header_name"]
    value = header["header_value"]

    if name in all_headers_1:
        values = all_headers_1[name]
        if not value==values[0]:
            filtering_stats["consistent_session"] += 1
            return False
        return True
    return False

def not_in_storage(header, all_headers_1, all_headers_2, seen_headers, storage_values, filtering_stats):
    if header["header_value"] not in storage_values:
        filtering_stats["not_in_storage"] += 1
        return False
    return True

def consistent_visits(header, all_headers_1, all_headers_2, seen_headers, storage_values, filtering_stats):
    name = header["header_name"]
    value = header["header_value"]

    if name in all_headers_2:
        values = all_headers_2[name]
        if not value==values[0]:
            filtering_stats["consistent_visits"] += 1
            return False
        return True
    return True


def url(header, all_headers_1, all_headers_2, seen_headers, storage_values, filtering_stats):
    value = header["header_value"]
    try:
        result = urlparse(value)
        return True if result.scheme in ("http", "https") and result.netloc else 0
    except:
        filtering_stats["url"] += 1
        return False

def entropy(header, all_headers_2, seen_headers, storage_values, filtering_stats):
    probs = [freq / len(header["header_value"]) for freq in Counter(header["header_value"]).values()]
    entropy_value = -sum(p * math.log2(p) for p in probs)
    if entropy_value < 3:
        filtering_stats["entropy"] += 1
        return False
    return True

#####################################
# Report
#####################################
def build_combination_report(stats, total_headers, output_file, label):
    report = {label: {}}
    for key, value in stats.items():
        report[label][key] = {
            "Headers into filter": total_headers,
            "Headers removed": value
        }
        total_headers = total_headers-value

    save_json(report, output_file)