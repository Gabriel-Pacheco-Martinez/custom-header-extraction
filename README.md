# 🕵️‍♂️ Detection of Tracking Custom Headers 

## 1. 📁 Project Architecture

The folder architecture of the project is the following

<pre>
log_collect_filter/
├── header_utils/
│ ├── file_io.py
│ ├── heuristic_filter.py           # Filtering pipeline with heuristics
│ ├── heuristic_stats.py
├── results/
│ ├── website1/
│ ├── website2/
│ ├── ...
│ ├── all_custom_headers.json       # Aggregated detected custom headers
├── header_analysis.py
├── main.py                         🔹 Main workflow controller
├── parser.py
ml_analysis/
├── feature_extractor.py            # Extracts features from "all_custom_headers.json"
├── header_features.csv
├── llm_analyzer.py                 # LLM-based analysis of headers
std_headers/
├── standard_headers.txt
├── std_headers_scraper.py
websites/
├── 5k-news-websites.txt
├── ... </pre>


## 2. 📄 Important Files

- 🔹 **main.py** – Main script that orchestrates the full workflow across websites.
- 🔹 **header_analysis.py** – Gateway for all operations performed on captured headers.
- **parser.py** – Parses cookies, local storage, and session storage to extract stored values.
- **header_utils/file_io.py** – Handles reading and writing of JSON files.
- **header_utils/heuristic_filter.py** – Implements the filtering heuristics for headers.
- **header_utils/heuristic_stats.py** – Collects statistics on the effect of each filter.
- **ml_analysis/feature_extractor.py** – Extracts structured features from captured logs.
- **ml_analysis/llm_analyzer.py** – Performs large language model (LLM) analysis on the extracted header features.
- **std_headers/std_headers_scraper.py** – Scrapes reference websites to generate `standard_headers.txt`.