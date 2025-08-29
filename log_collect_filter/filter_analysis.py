import os
import json
from collections import defaultdict

def aggregate_filter_stats(results_dir="results"):
    """
    Aggregates 'Headers removed' and 'Headers into filter' from all websites
    that have both 'capture' and 'capture2' folders.
    Returns a dictionary in the same structure as the original stats file,
    plus 'Resulting headers' for each heuristic.
    """
    total_stats = defaultdict(lambda: {"Headers into filter": 0, "Headers removed": 0})
    websites_considered = 0

    for website_name in os.listdir(results_dir):
        website_path = os.path.join(results_dir, website_name)
        if not os.path.isdir(website_path):
            continue

        # Only consider folders with both 'capture' and 'capture2'
        if not (os.path.isdir(os.path.join(website_path, "capture")) and
                os.path.isdir(os.path.join(website_path, "capture2"))):
            continue

        pipeline_file = os.path.join(website_path, "pipeline", "compound_filter_stats.json")
        if not os.path.isfile(pipeline_file):
            print(f"Warning: {pipeline_file} does not exist.")
            continue

        # Load JSON data
        with open(pipeline_file, "r") as f:
            data = json.load(f)

        stats = data.get("Compound filtering statistics", {})
        for heuristic, counts in stats.items():
            total_stats[heuristic]["Headers into filter"] += counts.get("Headers into filter", 0)
            total_stats[heuristic]["Headers removed"] += counts.get("Headers removed", 0)

        websites_considered += 1

    # Add 'Resulting headers' for each heuristic
    for heuristic, counts in total_stats.items():
        counts["Resulting headers"] = counts["Headers into filter"] - counts["Headers removed"]

    aggregated_data = {
        "Compound filtering statistics": dict(total_stats),
        "Websites considered": websites_considered
    }

    return aggregated_data


if __name__ == "__main__":
    results_dir = "results"
    aggregated_data = aggregate_filter_stats(results_dir)

    output_file = os.path.join(results_dir, "aggregated_compound_filter_stats.json")
    with open(output_file, "w") as f:
        json.dump(aggregated_data, f, indent=2)

    print(f"Aggregated stats saved to {output_file}")
    print(f"Number of websites considered: {aggregated_data['Websites considered']}")
