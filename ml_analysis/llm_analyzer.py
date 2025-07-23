from langchain_ollama import ChatOllama
import csv

llm = ChatOllama(model="qwen2.5:7b", base_url="http://localhost:11434", temperature=0.0)

# =====================
# Main
# =====================
if __name__ == "__main__":
    csv_file = "header_features.csv"

    with open(csv_file, newline='', encoding='latin1') as csv_file:
        reader = csv.DictReader(csv_file)

        for index, row in enumerate(reader):
            method = row.get("method", "").strip()
            header_name = row.get("header_name", "").strip()
            header_value = row.get("header_value", "").strip()

            # Counts
            header_name_length = row.get("header_name_length", "").strip()
            header_value_length = row.get("header_value_length", "").strip()
            num_letters_in_value = row.get("num_letters_in_value", "").strip()
            num_numbers_in_value = row.get("num_numbers_in_value", "").strip()
            num_special_chars_in_value = row.get("num_special_chars_in_value", "").strip()

            # Value characteristics
            value_is_uuid = row.get("value_is_uuid", "").strip()
            value_is_base64 = row.get("value_is_base64", "").strip()
            value_is_jwt = row.get("value_is_jwt", "").strip()
            value_has_email_or_phone = row.get("value_has_email_or_phone", "").strip()

            # Entropy analysis
            header_name_entropy = row.get("header_name_entropy", "").strip()
            header_value_entropy = row.get("header_value_entropy", "").strip()

            # Number of host domains
            num_sites_calling_header = row.get("host_domain_count", "").strip()

            prompt = f"""
            ###
            System prompt:
            You are an expert in classifying tracking HTTP headers based on the parameters given such as entropy,
            length, difference between host domain and method domain, and other given parameters. 

            *Important*: Vendor-specific headers used to process metadata, which have supporting documentation 
            and have the corresponding known safe values as header values, should NOT be considered tracking. 
            Always check if the header has official documentation before classifying

            Note: Higher entropy values (>3.0) in header names/values often indicate tracking identifiers

            ###
            User prompt:
            Please classify the header given in "current header information" using its parameters and your logic. 

            **MANDATORY STEPS**:
            1. First, check if this header has official documentation or is a known standard/vendor header
            2. If the header has official documentation and the header_values matches the safe/standard values classify as non-tracking
            3. If undocumented or has suspicious patterns, then use other metrics/parameters provided

            Provide your answer as a boolean indicating whether the header is tracking (`YES` or `NO`)

            Wrap your reasoning inside <think>...</think>, write a concise summary after, and then provide your final
            answer inside <answer>...</answer> tags.

            <think>
            STEP 1 - DOCUMENTATION CHECK:
            - Header name pattern analysis: [Is this a known documented header type? like X-Goog-Stored-Content-Encoding]
            - Known standards: [Check against, Google Cloud and other vendor documentation]
            - Documentation verdict: [DOCUMENTED/UNDOCUMENTED]

            STEP 2 - VALUE SAFETY CHECK (only if documented):
            - Value format analysis: [Does value match documented safe patterns? like gzip, identity for X-Goog-Stored-Content-Encoding]
            - Safety verdict: [SAFE/SUSPICIOUS]

            STEP 3 - METRICS ANALYSIS (only if undocumented or suspicious):
            - Entropy analysis: [High entropy = likely tracking]
            - Cross-domain analysis: [Different domains = likely tracking]
            - Format analysis: [UUID/Base64/JWT patterns]

            FINAL DECISION: [Based on documentation first, then metrics]
            </think>

            Summary: Based on the evidence, this header is tracking.
            <answer>YES</answer>
            <confidence>number: why</confidence> what you answer here is important because it will help
            me further develop my prompt/training

            **CONFIDENCE SCORING GUIDE**:
            - 0.95-1.0: Clear documentation exists, value matches safe patterns OR obvious tracking pattern
            - 0.80-0.94: Strong evidence from multiple indicators (entropy + format + cross-domain)
            - 0.60-0.79: Mixed signals, some uncertainty in classification
            - 0.40-0.59: Weak evidence, could go either way
            - 0.20-0.39: Very uncertain, limited information
            - 0.00-0.19: Unable to classify reliably

            **CONFIDENCE EXPLANATION CATEGORIES**:
            - "Has official documentation and safe value format"
            - "Multiple tracking indicators align (entropy + UUID + cross-domain)"
            - "Entropy suggests tracking but no other clear indicators"
            - "Documented header but suspicious value pattern"
            - "Insufficient information to classify reliably"
            - "Mixed signals - some tracking indicators, some legitimate patterns"

            ### Current header information
            - HTTP Method: {method}
            - Header Name: {header_name}
            - Header Value: {header_value}

            - Header Name Length: {header_name_length}
            - Header Value Length: {header_value_length}
            - Letters in Value: {num_letters_in_value}
            - Numbers in Value: {num_numbers_in_value}
            - Special Characters in Value: {num_special_chars_in_value}

            - Value is UUID: {value_is_uuid}
            - Value is Base64: {value_is_base64}
            - Value is JWT: {value_is_jwt}
            - Value Contains Email or Phone: {value_has_email_or_phone}

            - Header Name Entropy: {header_name_entropy}
            - Header Value Entropy: {header_value_entropy}
            - Number of Sites calling header: {num_sites_calling_header}
            """

            response = llm.invoke(prompt)

            print(f"{index + 1}.- {header_name}:\n")
            print(response.content)

            break