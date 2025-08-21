# General
import argparse
import os

# Mine
from log_collect_filter.web_crawler import perform_web_crawl
from ml_analysis.feature_extractor import perform_feature_extraction
from ml_analysis.llm_analyzer import analyse_headers_with_llm
from log_collect_filter.precollected_info_processor import perform_external_data_processing

# =====================
# Main
# =====================
if __name__ == "__main__":
    # ======
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Websites capture and processing.")
    parser.add_argument("--capture", action="store_true", help="Enable capture phase")
    parser.add_argument("--process", action="store_true", help="Enable processing phase")
    parser.add_argument("--file", type=str, default="5k-news-websites.txt", help="Path to the text file with website URLs")
    parser.add_argument("--threads", type=int, default=4, help="Number of threads")
    parser.add_argument("--llm", action="store_true", help="Enable llm analysis")
    parser.add_argument("--ext_process", action="store_true", help="Read an external file and process")
    args = parser.parse_args()

    # ======
    # Extract variables from argument
    capture = args.capture
    process = args.process
    file = os.path.join("websites", args.file)
    threads = args.threads
    analyze = args.llm
    external_process = args.ext_process

    # ======
    # Display information
    print("File being used: ", args.file)
    # print("Number of threads being used is: ", threads)

    # =====
    # Perform web crawl and process web info
    perform_web_crawl(file, capture, process, threads)

    # =====
    # Perform processing of previously collected data
    if external_process:
        perform_external_data_processing()

    # ====
    # Perform feature extraction and llm_analysis
    if analyze:
        perform_feature_extraction()
        analyse_headers_with_llm()
