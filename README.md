# 🕵️‍♂️ Detection of Tracking Custom Headers 

  -h, --help     show this help message and exit
  --capture      Enable capture phase
  --process      Enable processing phase
  --file FILE    Path to the text file with website URLs
  --llm          Enable llm analysis
  --ext_process  Read an external file and process


## 1. 🧪 Instructions

Follow these steps to run the full tracking header analysis pipeline:

### Step 1 — Collect Custom Headers
Run `main.py` inside the `log_collect_filter/` directory to generate `results/all_custom_headers.json`, which contains filtered custom headers.

```bash
cd log_collect_filter/
python main.py -help  # view arguments and usage
```

### Step 2 — Extract Header Features
Run `feature_extractor.py` in the `ml_analysis/` directory to extract feature data from the headers file generated in Step 1.

```bash
cd ml_analysis/
python feature_extractor.py
```

### Step 3 — Analyze with LLM
Run `llm_analyzer.py` in the `ml_analysis/` directory to apply LLM classification on the extracted features and generate an annotated CSV file.

```bash
python llm_analyzer.py
```

---

## 2. 📄 Resulting Files

| File Name                                       | Description                                              |
|-------------------------------------------------|----------------------------------------------------------|
| `results/all_custom_headers.json`               | Tracking headers obtained through the filtering pipeline |
| `ml_analysis/custom_header_features.csv`        | Extracted features from those headers & LLM analysis     |

## 3. 📁 Project Architecture

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


## 4. 🏃 Scripts

- 🔹 **main.py** – Main script that orchestrates the full workflow across websites.
- **header_analysis.py** – Gateway for all operations performed on captured headers.
- **parser.py** – Parses cookies, local storage, and session storage to extract stored values.
- **header_utils/file_io.py** – Handles reading and writing of JSON files.
- **header_utils/heuristic_filter.py** – Implements the filtering heuristics for headers.
- **header_utils/heuristic_stats.py** – Collects statistics on the effect of each filter.
- **ml_analysis/feature_extractor.py** – Extracts structured features from captured logs.
- **ml_analysis/llm_analyzer.py** – Performs large language model (LLM) analysis on the extracted header features.
- **std_headers/std_headers_scraper.py** – Scrapes reference websites to generate `standard_headers.txt`.