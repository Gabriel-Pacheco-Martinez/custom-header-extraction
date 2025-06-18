# Detection of Custom Headers

## Files

- **main.py** – Main script that orchestrates the full workflow across websites.
- **filter.py** – Contains all header filtering logic using heuristics.
- **parser.py** – Parses cookies, local storage, and session storage to extract stored values.
- **standardHeadersFileGenerator.py** – Scrapes reference websites to generate the list of standard headers "standard_headers.txt".

## Results

The `results/` folder has the following structure:

<pre> 
results/ 
├── all_custom_headers.json     # Custom headers found across all websites 
├── website1/ 
│ ├── custom_headers.json       # Custom headers found for this website 
│ ├── filter_stats.json         # Heuristic-based filtering attribution 
│ ├── network.json              # Raw network request/response events 
│ └── seen_std_headers.json     # Count of seen standard headers 
├── website2/ 
│ ├── ... </pre>