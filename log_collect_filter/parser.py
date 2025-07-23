import urllib.parse
import re
import json


def extract_all_cookie_values(cookies):
    # ======
    # Initialize set
    values = set()

    # ======
    # Loop
    for cookie in cookies:
        raw_value = cookie.get("value", "")
        if not raw_value:
            continue

        # Case 1: URL-encoded → decode and split
        if "%" in raw_value:
            decoded = urllib.parse.unquote(raw_value)
            parts = re.split(r"[|:$&]", decoded)
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                if "=" in part:
                    _, val = part.split("=", 1)
                    val = val.strip()
                    if val:
                        values.add(val)  # ✅ fixed
                else:
                    values.add(part)

        # Case 2: Not encoded but contains key=value → extract value from each pair
        elif "=" in raw_value:
            segments = re.split(r"[:|$&]", raw_value)  # Handle multi-field formats
            for seg in segments:
                if "=" in seg:
                    _, val = seg.split("=", 1)
                    val = val.strip()
                    if val:
                        values.add(val)
                else:
                    values.add(seg.strip())

        # Case 3: Plain unencoded value, no special structure
        else:
            values.add(raw_value.strip())

    return values

def extract_all_storage_values(data):
    # ======
    # Initialize set
    values = set()

    # ======
    # Recursion function
    def recurse(value):
        # If dictionary
        if isinstance(value, dict):
            for v in value.values():
                recurse(v)

        # If list
        elif isinstance(value, list):
            for elem in value:
                recurse(elem)

        # Else
        else:
            if not isinstance(value, str):
                values.add(value)
                return

            # Remove surrounding quotes
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]

            # Case 1: URL-encoded → decode and split
            if "%" in value:
                decoded = urllib.parse.unquote(value)
                parts = re.split(r"[|:$&]", decoded)
                for part in parts:
                    part = part.strip()
                    if not part:
                        continue
                    if "=" in part:
                        _, val = part.split("=", 1)
                        val = val.strip()
                        if val:
                            values.add(val)
                    else:
                        values.add(part)

            # Case 2: Not encoded but contains key=value → extract value from each pair
            elif "=" in value:
                segments = re.split(r"[:|$&]", value)  # Handle multi-field formats
                for seg in segments:
                    if "=" in seg:
                        _, val = seg.split("=", 1)
                        val = val.strip()
                        if val:
                            values.add(val)
                    else:
                        values.add(seg.strip())

            # Case 3: Plain unencoded value, no special structure
            else:
                values.add(value.strip())

    # ======
    # Recursion callback
    recurse(data)
    return values

def parse_nested_json(value):
    #=====
    # If it's a dict, parse each value recursively
    if isinstance(value, dict):
        new_dict = {}
        for k, v in value.items():
            # Fix mprtcl-v4
            if "mprtcl-v4" in k and isinstance(v, str):
                fixed = fix_and_parse_mprtcl(v)
                new_dict[k] = parse_nested_json(fixed)
            else:
                new_dict[k] = parse_nested_json(v)
        return new_dict

    # =====
    # If it's a list
    elif isinstance(value, list):
        return [parse_nested_json(elem) for elem in value]

    # =====
    # If it's a string, try parsing as JSON
    elif isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parse_nested_json(parsed)

        except (json.JSONDecodeError, TypeError):
            return value

    # =====
    else:
        return value

def fix_and_parse_mprtcl(value):
    value = value.replace("'", '"')
    value = value.replace('|', ',')
    value = re.sub(r',(\s*[}\]])', r'\1', value)

    value = value.strip()

    if not value:
        return value

    try:
        parsed = json.loads(value)
        return parsed
    except json.JSONDecodeError as e:
        print("JSON decode error:", e)
        return value