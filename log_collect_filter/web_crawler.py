# General
import os
import json
import time
import urllib.parse

# Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Mine
from log_collect_filter.header_utils.file_io import read_json, save_json, load_standard_headers
from log_collect_filter.parser import extract_all_cookie_values, parse_nested_json, extract_all_storage_values
from log_collect_filter.header_analysis import get_custom_headers, get_headers, get_headers_key_value_pair


# =====================
# Helper functions
# =====================
def visit_url(driver, url, wait_time=20):
    # driver.delete_all_cookies()
    try:
        time.sleep(1)  # Allow browser to settle
        driver.get(url)
    except Exception as e:
        print("[✗] Could not load:", url)
        print("    Error:", str(e))
    time.sleep(wait_time)

def get_hostname(url):
    try:
        return urllib.parse.urlparse(url).netloc.replace(":", "_")
    except:
        return "invalid"

def extract_network_events(logs):
    events = []
    for entry in logs:
        try:
            message = json.loads(entry["message"])["message"]
            if message["method"] in ["Network.requestWillBeSent", "Network.responseReceived"]:
                events.append(message)
        except (json.JSONDecodeError, KeyError):
            continue
    return events

def get_storage_information(driver):
    # Define set to store values
    storage_values = set()

    # Values in cookies/local/session storage
    cookies = driver.get_cookies()
    local_storage = parse_nested_json(driver.execute_script("return {...localStorage}"))
    session_storage = parse_nested_json(driver.execute_script("return {...sessionStorage}"))

    # Update set with values
    storage_values.update(extract_all_cookie_values(cookies))
    storage_values.update(extract_all_storage_values(local_storage))
    storage_values.update(extract_all_storage_values(session_storage))

    return storage_values, cookies, local_storage, session_storage

# =====================
# Capture sites
# =====================
def setup_driver():
    options = Options()
    #options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--auto-open-devtools-for-tabs")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd("Network.enable", {})
    return driver

def capture_site_data(url, base_output_folder):
    hostname = get_hostname(url)
    first_visit_successful = False
    second_visit_successful = False

    # ======
    # First visit
    driver = setup_driver()
    try:
        # ======
        # Capture folder
        capture_folder = os.path.join(base_output_folder, hostname + "/capture")

        # ======
        # Visit url
        visit_url(driver, url)

        # ======
        # Get storage information
        storage_values, cookies, local_storage, session_storage = get_storage_information(driver)

        # ======
        # Get network information
        logs = driver.get_log("performance")
        network_events = extract_network_events(logs)

        # ======
        # Extract headers
        all_headers = get_headers(network_events, hostname)
        all_headers_dict_1 = get_headers_key_value_pair(network_events)

        # =====
        # Save information
        data_to_save = [
            (network_events, "network_events.json"),
            (all_headers, "all_headers.json"),
            (cookies, "cookies.json"),
            (local_storage, "local_storage.json"),
            (session_storage, "session_storage.json"),
            (storage_values, "storage_values.json"),
            (all_headers_dict_1, "all_headers_dict_1.json")
        ]
        for data, filename in data_to_save:
            save_json(data, os.path.join(capture_folder, filename))

        print(f"[✓] Captured: {hostname} — 1st visit")
        first_visit_successful = True

    except Exception as e:
        print(f"[✗] Failed: {url} — {str(e)}")
    finally:
        driver.quit()

    # Short delay to stabilize
    time.sleep(0.1)

    # ======
    # Second visit
    driver = setup_driver()
    try:
        # ======
        # Capture folder
        capture_folder = os.path.join(base_output_folder, hostname + "/capture2")

        # ======
        # Visit url
        visit_url(driver, url)

        # ======
        # Get storage information
        storage_values, cookies, local_storage, session_storage = get_storage_information(driver)

        # ======
        # Get network information
        logs = driver.get_log("performance")
        network_events = extract_network_events(logs)

        # =====
        # Extract headers
        all_headers_dict_2 = get_headers_key_value_pair(network_events)

        # =====
        # Save information
        save_json(all_headers_dict_2, os.path.join(capture_folder, "all_headers_dict_2.json"))

        print(f"[✓] Captured: {hostname} — 2nd visit")
        second_visit_successful = True

    except Exception as e:
        print(f"[✗] Failed: {url} — {str(e)}")
    finally:
        driver.quit()

    # ======
    # Return state of retrieval
    return 1 if first_visit_successful and second_visit_successful else 0

def capture_multiple_sites(urls, result_base_folder="log_collect_filter/results"):
    successful_crawls = 0
    for index, url in enumerate(urls):
        print(f"🔍 Looking into website #{index + 1}...")
        retrieval_state = capture_site_data(url, result_base_folder)
        successful_crawls += retrieval_state

    # Print information
    print("\n=================")
    print("CAPTURE SUMMARY:")
    print("=================")
    print("total websites: ", len(urls))
    print("total successful website crawls: ", successful_crawls)

# =====================
# Process sites
# =====================
def process_site_data(url, base_output_folder):
    hostname = get_hostname(url)
    print(f"[🌐] Webpage: {hostname}")

    capture_folder = os.path.join(base_output_folder, hostname + "/capture")
    capture_folder_2 = os.path.join(base_output_folder, hostname + "/capture2")
    pipeline_folder = os.path.join(base_output_folder, hostname + "/pipeline")
    stats_folder = os.path.join(base_output_folder, hostname + "/stats")

    all_headers, all_headers_dict_1, all_headers_dict_2, storage_values, default_headers = (None, None, None, None, None)

    # =====
    # Read files to process headers
    try:
        all_headers = read_json(capture_folder + "/all_headers.json")
        all_headers_dict_1 = read_json(capture_folder + "/all_headers_dict_1.json")
        storage_values = set(read_json(capture_folder + "/storage_values.json"))
    except Exception as e:
        print(f"⚠️Folder does not exist. Visit was not successful: {e}")
        return 0, [], 0 # Return: failed status, empty custom_headers, 0 total headers

    try:
        all_headers_dict_2 = read_json(capture_folder_2+"/all_headers_dict_2.json")
    except Exception as e:
        print("⚠️File not found: 'all_headers_dict_2.json' → Second visit was not successful.")
        return 0, [], 0 # Return: failed status, empty custom_headers, 0 total headers

    try:
        default_headers = load_standard_headers("std_headers/standard_headers.txt")
    except Exception as e:
        print("⚠️ File not found: 'standard_headers.txt'")
        return 0, [], 0 # Return: failed status, empty custom_headers, 0 total headers

    # =====
    # Get custom headers and save information
    custom_headers, standard_headers = get_custom_headers(
        all_headers, all_headers_dict_1, all_headers_dict_2, default_headers, storage_values, pipeline_folder
    )

    data_to_save = [
        (custom_headers, "custom_headers.json"),
        (standard_headers, "standard_headers.json"),
    ]
    for data, filename in data_to_save:
        save_json(data, os.path.join(pipeline_folder, filename))

    # =====
    # Get filtering permutation statistics (comment when you don't want stats)
    #get_filtering_permutation_stats(all_headers, all_headers_2, default_headers, storage_values, stats_folder)

    return 1, custom_headers, len(all_headers)


def process_multiple_sites(urls, result_base_folder="log_collect_filter/results"):
    all_custom_headers = []
    num_total_headers = 0
    successful_website_retrievals = 0 # number of successful retrievals (both visits)
    for url in urls:
        retrieval_status, custom_headers_curr_url, all_headers_curr_url = process_site_data(url, result_base_folder)
        successful_website_retrievals += retrieval_status
        all_custom_headers.append(custom_headers_curr_url)
        num_total_headers = num_total_headers + all_headers_curr_url
    save_json(all_custom_headers, os.path.join(result_base_folder, "all_custom_headers.json"))

    num_custom_headers = sum(len(headers) for headers in all_custom_headers if headers)

    # Print information
    print("\n=================")
    print("PROCESS SUMMARY:")
    print("=================")
    print("total websites: ",len(urls))
    print("total successful website crawls: ", successful_website_retrievals)
    print("total headers: ", num_total_headers)
    print("total custom headers: ", num_custom_headers)

# =====================
# Main
# =====================
def perform_web_crawl(file, capture, process):
    # ======
    # Read list with websites
    websites = []
    with open(file, "r") as f:
        for line in f:
            website = f"https://www.{line.strip()}/"
            websites.append(website)

    # ======
    # Capture website, process information, or both
    if capture:
        capture_multiple_sites(websites)
    if process:
        process_multiple_sites(websites)