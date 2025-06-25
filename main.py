import os
import json
import time
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from webdriver_manager.chrome import ChromeDriverManager
from filter import filter_headers


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

def visit_url(driver, url, wait_time=60):
    driver.get(url)
    time.sleep(wait_time)

def get_performance_logs(driver):
    return driver.get_log("performance")

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

def get_cookies(driver):
    return driver.get_cookies()

def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def save_text(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        content = str(data)
        for part in content.split(','):
            f.write(part.strip() + "\n")

def get_hostname(url):
    try:
        return urllib.parse.urlparse(url).netloc.replace(":", "_")
    except:
        return "invalid"

def capture_site_data(url, base_output_folder):
    hostname = get_hostname(url)
    output_folder = os.path.join(base_output_folder, hostname)
    custom_headers = None

    driver = setup_driver()
    try:
        visit_url(driver, url)
        logs = get_performance_logs(driver)

        # ======
        # Network and storage information
        network_events = extract_network_events(logs)
        custom_headers, standard_headers, stored_values = filter_headers(
            network_events, hostname, driver, output_folder)

        # ======
        # Save information
        save_json(network_events, os.path.join(output_folder, "network.json"))
        save_json(custom_headers, os.path.join(output_folder, "custom_headers.json"))
        save_json(standard_headers, os.path.join(output_folder, "seen_std_headers.json"))

        # ======
        # Print local/cookies
        save_text(stored_values, os.path.join(output_folder, "stored_values.txt"))

        print(f"[✓] Captured: {hostname}")

    except Exception as e:
        print(f"[✗] Failed: {url} — {str(e)}")
        return []
    finally:
        driver.quit()
        return custom_headers

def capture_multiple_sites(urls, result_base_folder="results"):
    all_custom_headers = []
    for url in urls:
        custom_headers_curr_url = capture_site_data(url, result_base_folder)
        all_custom_headers.append(custom_headers_curr_url)

    save_json(all_custom_headers, os.path.join(result_base_folder, "all_custom_headers.json"))

# Example usage
if __name__ == "__main__":
    websites = [
        # =====
        "https://www.cloudflare.com/",
        "https://www.bbcamerica.com/", #✅
        "https://onedrive.com", #✅
        "https://www.nytimes.com/", #✅
        "https://www.businesstimes.com.sg/",
        "https://www.tiktok.com/explore", #✅
        "https://www.jasatel.net",
        "https://www.booking.com", #🔸
        "https://www.planfix.com", #✅
        "https://bedbathandbeyond.com",
        "https://www.bnnbloomberg.ca", #✅
        "https://www.amazon.com/", #✅
        "https://grand-stream.com/", #✅
        "https://www.eatthis.com/", #✅
        "https://www.orlandosentinel.com/",
        "https://www.foodandwine.com/", #✅
        "https://www.excite.co.jp/", #✅
        "https://response.jp/", #✅

        # =====
        # "https://news.google.com","https://bbc.co.uk","https://usatoday.com",
        # "https://bloomberg.com","https://time.com"
    ]
    capture_multiple_sites(websites)