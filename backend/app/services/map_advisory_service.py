import re
import requests


TRAVEL_ADVISORIES_URL = "https://cadataapi.state.gov/api/TravelAdvisories"


ADVISORY_LEVEL_TO_MAP_DATA = {
    1: {
        "mapScore": 90,
        "riskLevel": "Low",
        "condition": "Exercise normal precautions",
    },
    2: {
        "mapScore": 70,
        "riskLevel": "Medium",
        "condition": "Exercise increased caution",
    },
    3: {
        "mapScore": 45,
        "riskLevel": "High",
        "condition": "Reconsider travel",
    },
    4: {
        "mapScore": 20,
        "riskLevel": "High",
        "condition": "Do not travel",
    },
}


def get_default_map_data():
    return {
        "mapScore": None,
        "riskLevel": "Unknown",
        "condition": "No advisory data available",
    }


def extract_advisory_level(title: str):
    """
    Extracts the advisory level from title.

    Example:
    "Japan - Level 1: Exercise Normal Precautions"
    returns 1.
    """

    if not title:
        return None

    match = re.search(r"Level\s*([1-4])", title, re.IGNORECASE)

    if match is None:
        return None

    return int(match.group(1))


def extract_country_code(advisory):
    """
    Extracts the code from Category.

    Example:
    "Category": ["SG"]
    returns "sg".
    """

    category = advisory.get("Category")

    if not category:
        return None

    if isinstance(category, list) and len(category) > 0:
        return str(category[0]).lower()

    if isinstance(category, str):
        return category.lower()

    return None


def extract_country_name_from_title(title: str):
    """
    Extracts country name from the advisory title.

    Examples:
    "Japan - Level 1: Exercise Normal Precautions" -> "japan"
    "Mexico Travel Advisory - Level 2: Exercise Increased Caution" -> "mexico"
    """

    if not title:
        return None

    country_name = title

    # Remove everything from " - Level ..." onwards.
    country_name = re.sub(r"\s*-\s*Level\s*[1-4].*$", "", country_name, flags=re.IGNORECASE)

    # Remove "Travel Advisory" wording if present.
    country_name = country_name.replace("Travel Advisory", "")

    country_name = country_name.strip().lower()

    if not country_name:
        return None

    return country_name


def fetch_us_travel_advisories():
    """
    Fetches US travel advisories and stores each advisory using two possible keys:
    1. The advisory category code, e.g. "sg", "id", "ja"
    2. The country name from the title, e.g. "singapore", "indonesia", "japan"

    This avoids needing manual overrides for cases like Japan:
    ISO code is "jp", but the advisory feed category is "ja".
    """

    response = requests.get(TRAVEL_ADVISORIES_URL, timeout=10)

    # debug
    #print("US advisory status:", response.status_code)

    if response.status_code != 200:
        print("US advisory API error:", response.status_code, response.text)
        return {}

    advisories = response.json()
    advisory_map = {}

    for advisory in advisories:
        title = advisory.get("Title", "")

        country_code = extract_country_code(advisory)
        country_name = extract_country_name_from_title(title)
        advisory_level = extract_advisory_level(title)

        if advisory_level is None:
            continue

        map_data = ADVISORY_LEVEL_TO_MAP_DATA.get(
            advisory_level,
            get_default_map_data(),
        )

        # Store by advisory code, e.g. "sg", "id", "ja".
        if country_code is not None:
            advisory_map[country_code] = map_data

        # Also store by country name, e.g. "singapore", "indonesia", "japan".
        if country_name is not None:
            advisory_map[country_name] = map_data

    # debug
    # print("Loaded US advisory keys:", len(advisory_map))
    # print("US advisory map sample keys:", list(advisory_map.keys())[:20])

    return advisory_map


def get_map_data_for_destination(destination, advisory_map):
    """
    Gets mapScore/riskLevel/condition for one destination.

    First tries matching by 2-letter newsCode.
    If that fails, tries matching by country name.
    """

    news_code = destination.get("newsCode")
    country_name = destination.get("country", "").lower()

    if news_code:
        map_data = advisory_map.get(news_code.lower())

        if map_data is not None:
            return map_data

    if country_name:
        map_data = advisory_map.get(country_name)

        if map_data is not None:
            return map_data

    return get_default_map_data()