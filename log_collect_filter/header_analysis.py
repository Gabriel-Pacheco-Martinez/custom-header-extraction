import tldextract

from log_collect_filter.header_utils.heuristic_filter import filter_pipeline
from log_collect_filter.header_utils.heuristic_stats import filter_combinations

#####################################
# Get ALL headers in network
#####################################
def get_headers(events, hostname):
    all_headers = []
    hostname_domain = get_domain(hostname)

    # =======
    # Extract network headers
    for event in events:
        method = event.get("method")
        params = event.get("params")
        headers = None
        method_domain = None
        method_type = None

        if method == "Network.requestWillBeSent":
            request = params.get("request")
            request_url = request.get("url")
            method_domain = get_domain(request_url)
            headers = request.get("headers")
            method_type = "REQUEST"
        elif method == "Network.responseReceived":
            response = params.get("response")
            response_url = response.get("url")
            method_domain = get_domain(response_url)
            headers = response.get("headers")
            method_type = "RESPONSE"

        if headers:
            for header_name, header_value in headers.items():
                all_headers.append({
                    "method": method_type,
                    "header_name": header_name,
                    "header_value": header_value,
                    "host_domain": hostname_domain,
                    "method_domain": method_domain
                })

    return all_headers


def get_headers_key_value_pair(events):
    all_headers_2 = {}

    for event in events:
        method = event.get("method")
        params = event.get("params")
        headers = None

        if method == "Network.requestWillBeSent":
            request = params.get("request")
            headers = request.get("headers")

        elif method == "Network.responseReceived":
            response = params.get("response")
            headers = response.get("headers")

        if headers:
            for header_name, header_value in headers.items():
                all_headers_2[header_name] = header_value

    return all_headers_2


#####################################
# Get CUSTOM headers through filtering
#####################################
def get_custom_headers(all_headers, all_headers_2, default_headers, storage_values, pipeline_folder):
    # =======
    # Perform custom header extraction
    custom_headers, standard_headers = filter_pipeline(
        all_headers, all_headers_2, default_headers, storage_values, pipeline_folder
    )
    return custom_headers, standard_headers

#####################################
# Get PERMUTATION filtering stats
#####################################
def get_filtering_permutation_stats(all_headers, all_headers_2, default_headers, storage_values, stats_folder):
    # =======
    # Get statistics
    filter_combinations(
        all_headers, all_headers_2, default_headers, storage_values, stats_folder
    )

#####################################
# Helper Functions
#####################################
def get_domain(url):
    try:
        return tldextract.extract(url).top_domain_under_public_suffix
    except:
        return "invalid"