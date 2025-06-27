import itertools
import urllib.parse
import os
from information_api import save_json

#####################################
# Permutations
#####################################
def permutation_statistics(all_headers, known_standard_headers, storage_values, output_folder):
    filters = [third_party, min_length, consistent, not_in_storage]
    n=1

    for r in range(1, len(filters)+1):
        for combo in itertools.combinations(filters,r):
            filtering_stats = {
                "third_party": 0,
                "min_length": 0,
                "consistent": 0,
                "not_in_storage": 0
            }
            seen_headers = {}
            surviving_headers = []

            for header in all_headers:
                passed = True

                for curr_func in combo:
                    if not curr_func(header, seen_headers, storage_values, filtering_stats):
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
def third_party(header, seen_headers, storage_values, filtering_stats):
    if header["host_domain"] == header["method_domain"]:
        filtering_stats["third_party"] += 1
        return False
    return True

def min_length(header, seen_headers, storage_values, filtering_stats):
    if len(urllib.parse.unquote(header["header_value"])) >= 8:
        filtering_stats["min_length"] += 1
        return False
    return True

def consistent(header, seen_headers, storage_values, filtering_stats):
    if header["header_name"] in seen_headers:
        if seen_headers[header["header_name"]] != header["header_value"]:
            filtering_stats["consistent"] += 1
            return False
    else:
        seen_headers[header["header_name"]] = header["header_value"]
    return True

def not_in_storage(header, seen_headers, storage_values, filtering_stats):
    if header["header_value"] not in storage_values:
        filtering_stats["not_in_storage"] += 1
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