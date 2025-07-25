from langchain_ollama import ChatOllama
import re
import pandas as pd

def analyse_headers_with_llm():

    llm = ChatOllama(model="qwen2.5:7b", base_url="http://localhost:11434", temperature=0.0)

    # =======
    # Read csv
    csv_file = "custom_header_features.csv"
    df = pd.read_csv(csv_file)

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
        System prompt:
        You are an expert in classifying tracking HTTP headers based on the parameters given.
    
        ###
        User prompt:
        Please classify the header given in "current header information" using the parameters with your logic.
    
        Provide your answer in the following format:
        <answer>Boolean indicating whether the header is tracking (`YES` or `NO`).</answer>
        <confidence>Confidence for the classification as a number.</confidence>
        <logic>Provide your conclusion logic. I will later on use this conclusion to keep training you.</logic>
    
        ### Current header information
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
    
        # - Header Name Entropy: {str(row.get("header_name_entropy", "")).strip()}
        # - Header Value Entropy: {str(row.get("header_value_entropy", "")).strip()}
    
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
    df.to_csv(csv_file, index=False)

# =====================
# Main
# =====================
if __name__ == "__main__":
    analyse_headers_with_llm()