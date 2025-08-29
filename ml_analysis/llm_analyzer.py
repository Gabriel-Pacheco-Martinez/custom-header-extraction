from langchain_ollama import ChatOllama
import re
import os
import pandas as pd
import json
from collections import Counter, defaultdict

def analyse_headers_with_llm():
    # Print information
    print("\n=================")
    print("LLM ANALYSIS:")
    print("=================")

    # =======
    # Model
    model_name = "qwen2.5:7b"
    llm = ChatOllama(model=model_name, base_url="http://localhost:11434", temperature=0.0)

    # =======
    # Read csv
    input_csv = "ml_analysis/csv_files_before_models/tracking_headers.csv"
    df = pd.read_csv(input_csv)

    if df.empty:
        print("⚠️ Analyzer: CSV file has no data.")
        exit(0)

    # =======
    # Output csv
    output_csv = f"ml_analysis/csv_files_post_models/{model_name.split(':')[0]}.csv"
    output_json = f"ml_analysis/json_files/{model_name.split(':')[0]}.json"
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    os.makedirs(os.path.dirname(output_json), exist_ok=True)

    # =======
    # Prepare new columns
    df["is_tracking"] = ""
    df["confidence"] = ""
    df["why"] = ""

    # JSON results list
    json_results = []

    # =======
    # Iterate
    for index, row in df.iterrows():
        header_name = str(row.get("header_name", "")).strip()
        header_value = str(row.get("header_value", "")).strip()

        # =========
        # Call to LLM
        prompt = f"""
        ###
        Context:
        In HTTP communication, headers are key-value pairs exchanged in requests and responses. Standard headers (e.g., Content-Type, Authorization) serve functional purposes like authentication, caching, and content negotiation. These do not contain identifying information by default.

        Custom headers are application-specific fields that support debugging, feature toggles, client versioning, or metadata. These are not meant to track or identify users.

        However, custom headers can be co-opted for tracking: identifying users, linking sessions, building behavioral profiles, and bypassing browser privacy mechanisms via cross-origin leaks. These are called tracking headers.

        ###
        Examples:
        Below are two examples of **tracking headers**.

        - method: REQUEST
          name: x-mp-key
          value: us1-4d67df7096df824194bb46893e83f1c9
          name_length: 8
          value_length: 36
          letters: 12
          numbers: 23
          special_chars: 1
          is_uuid: false
          is_base64: false
          is_jwt: false
          consistent across visits: true
          value in storage: true
          host_domains: [bbcamerica.com]
          destination_domains: [mparticle.com]

        - method: RESPONSE
          name: x-advertisable-eid
          value: 3QEU55AVURGVNFYKGPRLHU
          name_length: 18
          value_length: 22
          letters: 19
          numbers: 3
          special_chars: 0
          is_uuid: false
          is_base64: true
          is_jwt: false
          consistent across visits: true
          value in storage: true
          host_domains: [planfix.com]
          destination_domains: [adroll.com]

        Below are two examples of **non-tracking headers**.

        - method: RESPONSE
          name: x-dw-request-base-id
          value: z3oXAL9xgmgBAAB_
          name_length: 20
          value_length: 16
          letters: 13
          numbers: 2
          special_chars: 1
          is_uuid: false
          is_base64: false
          is_jwt: false
          consistent across visits: false
          value in storage: false
          host_domains: [nautica.com]
          destination_domains: [nautica.com]

        - method: RESPONSE
          name: x-akamai-transformed
          value: "9 - 0 pmb=mRUM,2"
          name_length: 20
          value_length: 16
          letters: 7
          numbers: 3
          special_chars: 6
          is_uuid: false
          is_base64: false
          is_jwt: false
          consistent across visits: true
          value in storage: false
          host_domains: [nautica.com]
          destination_domains: [nautica.com]

        ###
        System Prompt:
        You are an expert at classifying whether an HTTP header is used for tracking, **based only on the parameters provided** — not on the name of the header.

        ###
        User Prompt:
        Please classify the header below based solely on the provided parameters, using logical reasoning.

        **Heuristics to consider:**
        1. Third-party destination domain (destination domains different from host domains). Also take into account if the destination domain is known for tracking.
        2. Length and composition of the value (long values, mix of letters, numbers, special chars)
        3. Encoded values (Base64, UUID, JWT)
        4. Consistency across session and visits
        5. Stored in browser storage

        Instructions:
        - Base your decision only on the given heuristics and any obvious additional indicators.
        - Your response must strictly follow the format below.
        - The <answer> must contain only YES or NO.
        - The <confidence> must be a number between 0 and 100.
        - The <logic> section should explain the reasoning in full sentences. Do NOT put any reasoning in the heuristics section.
        - In the <heuristics> section, write ONLY YES or NO for each heuristic. No extra words.

        **Output format**
        <answer>YES or NO</answer>
        <confidence>[number between 0 and 100]</confidence>
        <logic>[Explain how the combination of heuristics influenced your decision]</logic>
        <heuristics>
        1. Third-party destination domain: YES/NO
        2. Length and composition: YES/NO
        3. Encoded values: YES/NO
        4. Consistency across visits: YES/NO
        5. Stored in cookies or local storage: YES/NO
        </heuristics>
        
        ### Current Header Information
        - HTTP Method: {str(row.get("method", "")).strip()}
        - Header Name: {str(row.get("header_name", "")).strip()}
        - Header Value: {str(row.get("header_value", "")).strip()}

        - Header Name Length: {str(row.get("header_name_length", "")).strip()}
        - Header Value Length: {str(row.get("header_value_length", "")).strip()}
        - Letters in Value: {str(row.get("num_letters_in_value", "")).strip()}
        - Numbers in Value: {str(row.get("num_numbers_in_value", "")).strip()}
        - Special Characters in Value: {str(row.get("num_special_chars_in_value", "")).strip()}

        - Value is UUID: {str(row.get("value_is_uuid", "")).strip()}
        - Value is Base64: {str(row.get("value_is_base64", "")).strip()}
        - Value is JWT: {str(row.get("value_is_jwt", "")).strip()}
        
        - Consistent across session and visits: {str(row.get("consistency_across_visits", "")).strip()}
        - Value in storage: {str(row.get("stored_in_cookies_or_local", "")).strip()}

        - Hosts domains: {str(row.get("host_domains", "")).strip()}
        - Destination domains: {str(row.get("destination_domains", "")).strip()}
        """

        response = llm.invoke(prompt)
        response_text = response.content

        print("==========")
        print(f"{index + 1}.- {header_name}:\n")
        print(response_text)

        # =========
        # Extract values from response
        answer = re.search(r"<answer>(.*?)</answer>", response_text, re.DOTALL)
        answer_text = answer.group(1).strip() if answer else "N/A"
        df.at[index, "is_tracking"] = answer_text

        confidence = re.search(r"<confidence>(.*?)</confidence>", response_text, re.DOTALL)
        confidence_text = confidence.group(1).strip() if confidence else "N/A"
        df.at[index, "confidence"] = confidence_text

        logic = re.search(r"<logic>(.*?)</logic>", response_text, re.DOTALL)
        logic_text = logic.group(1).strip() if logic else "N/A"
        df.at[index, "why"] = logic_text

        heuristics_match = re.search(r"<heuristics>(.*?)</heuristics>", response_text, re.DOTALL)
        heuristics_text = heuristics_match.group(1).strip() if heuristics_match else ""
        # Parse heuristics lines into a dict
        heuristics_dict = {}
        for line in heuristics_text.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                heuristics_dict[key.strip()] = value.strip()

        # Add to JSON results
        json_results.append({
            "header_name": header_name,
            "header_value": header_value,
            "prediction": answer_text,
            "heuristics": heuristics_dict
        })

    # Write updated dataframe to the same CSV file
    df.to_csv(output_csv, index=False)

    # Write JSON
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(json_results, f, indent=2)
    print(f"✅ JSON saved to {output_json}")

def summarize_json_predictions(json_file_path="json_files/qwen2.5.json"):
    """
    Reads the JSON file created by the LLM analysis and summarizes:
      - How many times each heuristic was YES or NO
      - How many times the prediction was YES or NO
    """
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Counters
    prediction_counter = Counter()
    heuristic_counter = defaultdict(Counter)

    for entry in data:
        # Count prediction YES/NO
        pred = entry.get("prediction", "N/A").upper()
        if pred in ["YES", "NO"]:
            prediction_counter[pred] += 1

        # Count heuristics YES/NO
        heuristics = entry.get("heuristics", {})
        for key, value in heuristics.items():
            val = value.upper()
            if val in ["YES", "NO"]:
                heuristic_counter[key][val] += 1

    # Print summary
    print("=== Prediction Summary ===")
    print(f"YES: {prediction_counter.get('YES',0)}")
    print(f"NO: {prediction_counter.get('NO',0)}\n")

    print("=== Heuristic Summary ===")
    for h, counts in heuristic_counter.items():
        print(f"{h}: YES={counts.get('YES',0)}, NO={counts.get('NO',0)}")

    return prediction_counter, heuristic_counter

# =====================
# Main
# =====================
if __name__ == "__main__":
    analyse_headers_with_llm()
    summarize_json_predictions()