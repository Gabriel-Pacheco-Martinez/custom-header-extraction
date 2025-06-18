import urllib.parse

def extract_inner_values(cookie_value):
    values = []

    # Try colon-separated key=value pairs
    if ':' in cookie_value and '=' in cookie_value:
        parts = cookie_value.split(':')
        for part in parts:
            if '=' in part:
                _, v = part.split('=', 1)
                values.append(v)
        if values:
            return values

    # Try JSON (possibly URL-encoded)
    try:
        decoded = urllib.parse.unquote(cookie_value)
        parsed = json.loads(decoded)
        if isinstance(parsed, dict):
            return list(parsed.values())
    except Exception:
        pass

    # Fallback: return original as single-item list
    return [cookie_value]

def extract_all_cookie_values(cookies):
    all_values = []
    for cookie in cookies:
        value_field = cookie.get("value", "")
        values = extract_inner_values(value_field)
        all_values.extend(values)
    return all_values

import json

def extract_all_storage_session_values(data):
    values = set()

    def recurse(val):
        if isinstance(val, dict):
            for v in val.values():
                recurse(v)
        elif isinstance(val, list):
            for item in val:
                recurse(item)
        elif isinstance(val, str):
            # Attempt to parse as JSON
            try:
                parsed = json.loads(val)
                recurse(parsed)
            except (json.JSONDecodeError, TypeError):
                values.add(val)
        else:
            values.add(val)

    for key, val in data.items():
        recurse(val)

    return values