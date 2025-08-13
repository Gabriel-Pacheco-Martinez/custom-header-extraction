from langchain_ollama import ChatOllama
import re
import os
import pandas as pd

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
        print("⚠️ Analyzer: CSV file has only header columns, no data rows.")
        exit(0)

    # =======
    # Output csv
    output_csv = f"ml_analysis/csv_files_post_models/{model_name.split(":")[0]}.csv"
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    # =======
    # Prepare new columns
    df["is_tracking"] = ""
    df["confidence"] = ""
    df["why"] = ""

    # =======
    # Iterate
    for index, row in df.iterrows():
        header_name = str(row.get("header_name", "")).strip()

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
          host_domains: [nautica.com]
          destination_domains: [nautica.com]

        ###
        System Prompt:
        You are an expert at classifying whether an HTTP header is used for tracking, **based only on the parameters provided** — not on the name of the header.

        ###
        User Prompt:
        Please classify the header below based solely on the provided parameters, using logical reasoning.

        Provide your answer in this format:

        <answer>YES or NO</answer>  
        <confidence>Give a number from 0 to 100 indicating your certainty in the classification.</confidence>  
        <logic>Your reasoning for this classification</logic>  

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
        df.at[index, "is_tracking"] = answer.group(1).strip() if answer else "N/A"

        confidence = re.search(r"<confidence>(.*?)</confidence>", response_text, re.DOTALL)
        df.at[index, "confidence"] = confidence.group(1).strip() if confidence else "N/A"

        logic = re.search(r"<logic>(.*?)</logic>", response_text, re.DOTALL)
        df.at[index, "why"] = logic.group(1).strip() if logic else "N/A"

    # Write updated dataframe to the same CSV file
    df.to_csv(output_csv, index=False)

# =====================
# Main
# =====================
if __name__ == "__main__":
    analyse_headers_with_llm()