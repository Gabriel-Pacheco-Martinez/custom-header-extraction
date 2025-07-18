# General
import os
import json
import time
import urllib.parse
from operator import truediv

# Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager

# Mine
from information_api import read_json, save_json, load_standard_headers
from parser import extract_all_cookie_values, parse_nested_json, extract_all_storage_values
from header_analysis import get_custom_headers, get_headers, get_filtering_permutation_stats

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
    #options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def capture_site_data(url, base_output_folder):
    hostname = get_hostname(url)
    capture_folder = os.path.join(base_output_folder, hostname + "/capture")
    driver = setup_driver()

    try:
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
        all_headers = get_headers(network_events, hostname)

        # =====
        # Save information
        data_to_save = [
            (network_events, "network_events.json"),
            (all_headers, "all_headers.json"),
            (cookies, "cookies.json"),
            (local_storage, "local_storage.json"),
            (session_storage, "session_storage.json"),
            (storage_values, "storage_values.json")
        ]
        for data, filename in data_to_save:
            save_json(data, os.path.join(capture_folder, filename))

        print(f"[✓] Captured: {hostname}")

    except Exception as e:
        print(f"[✗] Failed: {url} — {str(e)}")
        return []
    finally:
        driver.quit()

def capture_multiple_sites(urls, result_base_folder="results"):
    for url in urls:
        capture_site_data(url, result_base_folder)

# =====================
# Process sites
# =====================
def process_site_data(url, base_output_folder):
    hostname = get_hostname(url)
    print(f"[🌐] Webpage: {hostname}")

    capture_folder = os.path.join(base_output_folder, hostname + "/capture")
    pipeline_folder = os.path.join(base_output_folder, hostname + "/pipeline")
    stats_folder = os.path.join(base_output_folder, hostname + "/stats")

    # =====
    # Read files to process headers
    all_headers = read_json(capture_folder+"/all_headers.json")
    default_headers = load_standard_headers("standard_headers.txt")
    storage_values = set(read_json(capture_folder+"/storage_values.json"))

    # =====
    # Get custom headers and save information
    custom_headers, standard_headers = get_custom_headers(
        all_headers, default_headers, storage_values, pipeline_folder
    )

    data_to_save = [
        (custom_headers, "custom_headers.json"),
        (standard_headers, "standard_headers.json"),
    ]
    for data, filename in data_to_save:
        save_json(data, os.path.join(pipeline_folder, filename))

    # =====
    # Get filtering permutation statistics
    get_filtering_permutation_stats(all_headers, default_headers, storage_values, stats_folder)


    return custom_headers, len(all_headers)


def process_multiple_sites(urls, result_base_folder="results"):
    all_custom_headers = []
    num_total_headers = 0
    for url in urls:
        custom_headers_curr_url, all_headers_curr_url = process_site_data(url, result_base_folder)
        all_custom_headers.append(custom_headers_curr_url)
        num_total_headers = num_total_headers + all_headers_curr_url
    save_json(all_custom_headers, os.path.join(result_base_folder, "all_custom_headers.json"))

    num_custom_headers = sum(len(headers) for headers in all_custom_headers if headers)

    # Print information
    print("\n==========")
    print("total websites: ",len(urls))
    print("total headers: ", num_total_headers)
    print("total custom headers: ", num_custom_headers)

# =====================
# Main
# =====================
if __name__ == "__main__":
    # ======
    # Please change flags as needed
    capture = False  # Can be false if network information already available in folder "results/website/capture"
    process = True

    # ======
    # Define websites
    websites = [
        # =====
        "http://www.bbcamerica.com/",
        "http://www.planfix.com/",
        "http://bnnbloomberg.ca/",
        "http://wikipedia.org",
        "http://reddit.com",
        "http://bing.com/",
        "http://www.amazon.com/",
        "http://www.yahoo.com/",
        "http://www.temu.com",
        "http://www.duckduckgo.com/",
        "http://www.tiktok.com/",
        "http://www.yandex.ru/",
        "http://www.weather.com/",
        "http://www.msn.com/",
        "http://www.fandom.com/",
        "http://www.netflix.com/",
        "http://www.pinterest.com/",
        "http://www.naver.com/",
        "http://www.canva.com/",
        "http://www.vk.com/",
        "http://www.paypal.com/",
        "http://www.imdb.com/",
        "http://www.samsung.com/",
        "http://www.mail.ru/",
        "http://www.ebay.com/",
        "http://www.walmart.com/",
        "http://www.bbc.co.uk/",
        "http://www.amazon.de/",
        "http://www.google.com.br/",
        "http://www.amazon.co.uk/",
        "http://www.ozon.ru/",
        "http://www.cricbuzz.com/",
        "http://www.accuweather.com/",
        "http://www.etsy.com/",
        "http://www.uol.com.br/",
        "http://www.dzen.ru/",
        "http://www.shopify.com/",
        "http://www.steamcommunity.com/",
        "http://www.infobae.com/",
        "http://www.google.de/",
        "http://www.primevideo.com/",
        "http://www.dailymail.co.uk/",
        "http://www.linktree.ee/",
        "http://www.people.com/",
        "http://www.google.it/",
        "http://www.google.es/",
        "http://www.shein.com/",
        "http://www.max.com/",
        "http://www.avito.ru/",
        "http://www.twitch.tv/",
        "http://www.openai.com/",
        "http://www.aliexpress.com/",
        "http://www.github.com/",
        "http://www.spotify.com/",
        "http://www.apple.com/",
        "http://www.bilibili.com/",
        "http://www.roblox.com/",
        "http://www.globo.com/",
        "http://www.amazon.co.jp/",
        "http://www.nytimes.com/",
        "http://www.quora.com/",
        "http://www.telegram.org/",
        "http://www.dailymotion.com/",
        "http://www.coupang.com/",
        "http://www.booking.com/",
        "http://www.espn.com/",
        "http://www.brave.com/",
        "http://www.cnn.com/",
        "http://www.indeed.com/",
        "http://www.rakuten.co.jp/",
        "http://www.zoom.us/",
        "http://www.usps.com/",
        "http://www.steampowered.com/",
        "http://www.shop.app/",
        "http://www.marca.com/",
        "http://www.rutube.ru/",
        "http://www.ecosia.org/",
        "http://www.disneyplus.com/",
        "http://www.theguardian.com/",
        "http://www.gmail.com/",
        "http://www.zillow.com/",
        "http://www.amazon.in/",
        "http://www.instructure.com/",
        "http://www.wildberries.ru/",
        "http://www.google.co.uk/", #✅
    ]

    # ======
    # Capture website, process information, or both
    if capture:
        capture_multiple_sites(websites)
    if process:
        process_multiple_sites(websites)