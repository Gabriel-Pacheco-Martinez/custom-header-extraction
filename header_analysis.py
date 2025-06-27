import tldextract

from pipeline_filtering import heuristics_filtering_pipeline
from permutation_filtering_stats import permutation_statistics

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

#####################################
# Get CUSTOM headers through filtering
#####################################
def get_custom_headers(all_headers, default_headers, storage_values, pipeline_folder):
    # =======
    # Perform custom header extraction
    custom_headers, standard_headers = heuristics_filtering_pipeline(
        all_headers, default_headers, storage_values, pipeline_folder
    )
    return custom_headers, standard_headers

#####################################
# Get PERMUTATION filtering stats
#####################################
def get_filtering_permutation_stats(all_headers, default_headers, storage_values, stats_folder):
    # =======
    # Get statistics
    permutation_statistics(
        all_headers, default_headers, storage_values, stats_folder
    )

#####################################
# Helper Functions
#####################################
def get_domain(url):
    try:
        return tldextract.extract(url).top_domain_under_public_suffix
    except:
        return "invalid"