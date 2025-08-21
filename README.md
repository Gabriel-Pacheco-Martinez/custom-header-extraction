# 🕵️‍♂️ Detection of Tracking Custom Headers 

```
  -h, --help     show this help message and exit
  --capture      Enable capture phase
  --process      Enable processing phase
  --file FILE    Path to the text file with website URLs
  --llm          Enable llm analysis
  --ext_process  Read an external file and process
  --threads N    Define the number of threads for LLM part
```

## 1. 🧪 Instructions

### Step 1 — Activate virtual environment
Activate the `virtual environment`
```bash
source myenv/bin/activate
```

### Step 2 — Crawl websites
Run `main.py` to only crawl websites

```bash
python3 main.py --capture 
```

If a different file from the default is desired
```bash
python3 main.py --capture --file FILE 
```

### Step 3 — Process data fromm crawl

```bash
python3 main.py --process --llm
```

If code is desired to be run in parallel can be done with --threads N_of_threads
```bash
python3 main.py --process --llm --threads 10
```

---

## 2. 📄 Resulting Files

| File Name                               | Description                                              |
|-----------------------------------------|----------------------------------------------------------|
| `results/all_custom_headers.json`       | Tracking headers obtained through the filtering pipeline |
| `ml_analysis/custom_files_post_models/` | Extracted features from those headers & LLM analysis     |

## 3. 📁 Project Architecture

The folder architecture of the project is the following

<pre>
main.py                         🔹 Main workflow controller
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
├── precollected_info_processor.py                         
├── parser.py
├── web_crawler.py
ml_analysis/
├── csv_files_before_models/
├── csv_files_post_models/
├── feature_extractor.py            # Extracts features from "all_custom_headers.json"
├── llm_analyzer.py                 # LLM-based analysis of headers
std_headers/
├── standard_headers.txt
├── std_headers_scraper.py
websites/
├── 5k-news-websites.txt
├── ... </pre>


## 4. 🏃 Scripts

- 🔹 **main.py** – Main script that orchestrates the full workflow across websites.