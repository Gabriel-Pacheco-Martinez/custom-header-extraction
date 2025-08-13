# General
import argparse
import os

# Mine
from log_collect_filter.web_crawler import perform_web_crawl
from ml_analysis.feature_extractor import perform_feature_extraction
from ml_analysis.llm_analyzer import analyse_headers_with_llm

# =====================
# Main
# =====================
if __name__ == "__main__":
    # ======
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Websites capture and processing.")
    parser.add_argument("--capture", action="store_true", help="Enable capture phase")
    parser.add_argument("--process", action="store_true", help="Enable processing phase")
    parser.add_argument("--file", type=str, default="test.txt", help="Path to the text file with website URLs")
    parser.add_argument("--llm", action="store_true", help="Enable llm analysis")
    parser.add_argument("--hadi", action="store_true", help="Process Hadi's file")
    args = parser.parse_args()

    # ======
    # Extract variables from argument
    capture = args.capture
    process = args.process
    file = os.path.join("websites", args.file)
    analyze = args.llm
    hadi = args.hadi

    # =====
    # Perform web crawl and process web info
    perform_web_crawl(file, capture, process)

    # ====
    # Perform feature extraction and llm_analysis
    if analyze:
        perform_feature_extraction()
        analyse_headers_with_llm()
