import requests
from bs4 import BeautifulSoup
import re

def is_probable_header(text):
    http_methods = {
        'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD', 'CONNECT', 'TRACE'
    }

    return (
        text and
        not re.match(r"^\d{3}\s", text) and
        text not in http_methods and
        not text.lower().startswith("reason:") and
        not text.startswith("http-equiv") and
        re.match(r"^[A-Z][A-Za-z0-9\-]*$", text)  # Accept things like "Via", "Vary", "X-Header"
    )

def fetch_mdn_headers():
    url = "https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    headers = set()
    for code_tag in soup.find_all("code"):
        if code_tag.parent.name == "a":  # ensure it's a linked header name
            text = code_tag.get_text().strip()
            if is_probable_header(text):
                headers.add(text)
    return headers

def fetch_rfc_headers():
    url = "https://www.rfc-editor.org/rfc/rfc4229.html"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    headers = set()

    for span in soup.find_all("span", class_="h4"):
        text = span.get_text(strip=True)
        if "Header field:" in text:
            # Split and get the part after "Header field:"
            part = text.split("Header field:")[-1].strip()
            headers.add(part)

    return headers

def create_headers_file(output_txt_file="standard_headers.txt"):
    mdn_headers = fetch_mdn_headers()
    rfc_headers = fetch_rfc_headers()

    all_headers = mdn_headers.union(rfc_headers)

    # Save to text file
    with open(output_txt_file, "w") as f:
        for header in sorted(all_headers):
            f.write(header + "\n")

    print(f"Saved {len(all_headers)} headers to {output_txt_file}")

if __name__ == "__main__":
    # This block only runs when you execute this file directly
    create_headers_file()