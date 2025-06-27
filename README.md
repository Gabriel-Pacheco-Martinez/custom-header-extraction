# Detection of Custom Headers

## Files

- **main.py** – Main script that orchestrates the full workflow across websites.
- **header_analysis.py** – Gateway to all the operations that are performed on the headers.
- **pipeline_filtering.py** - Script that enforces the filtering pipeline
- **permutation_filtering_stats.py** - Does all the combinations of filters and collects data.
- **parser.py** – Parses cookies, local storage, and session storage to extract stored values.
- **information_api.py** - To read and write from and to files.
- **standardHeadersFileGenerator.py** – Scrapes reference websites to generate the list of standard headers "standard_headers.txt".

## Results

The `results/` folder has the following structure:

<pre> 
results/ 
├── all_custom_headers.json         # Custom headers found across all websites 
├── website1/ 
│ ├── capture/          # All network/application information
│ ├── pipeline/         # Filtering information
│ └── stats/            # Statistics for combinations of filters
├── website2/ 
│ ├── ... </pre>