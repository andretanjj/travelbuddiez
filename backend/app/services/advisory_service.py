import re
import requests

# US travel advisory API
TRAVEL_ADVISORIES_URL = "https://cadataapi.state.gov/api/TravelAdvisories"


"""
Converts US advisory levels into map-friendly data.
Used by MapView for country coloring and tooltip.
"""
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
    """
    Returns default map data when no advisory is avaialble.
    This prevents frontend from crashing if a country has no advisory matches.
    """
    return {
        "mapScore": None,
        "riskLevel": "Unknown",
        "condition": "No advisory data available",
        "advisoryLevel": None,
        "advisory": "No advisory information is available for this destination yet.",
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

    Eg:
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
    response = requests.get(
        TRAVEL_ADVISORIES_URL,
        timeout=10,
    )

    if response.status_code != 200:
        print(
            "US advisory API error:",
            response.status_code,
            response.text,
        )
        return {}

    advisories = response.json()
    advisory_map = {}

    for advisory in advisories:
        title = advisory.get("Title", "")
        country_name = extract_country_name_from_title(title)
        advisory_level = extract_advisory_level(title)

        if country_name is None or advisory_level is None:
            continue

        map_data = ADVISORY_LEVEL_TO_MAP_DATA.get(
            advisory_level,
            get_default_map_data(),
        )

        advisory_map[country_name] = {
            "mapScore": map_data["mapScore"],
            "riskLevel": map_data["riskLevel"],
            "condition": map_data["condition"],
            "advisoryLevel": advisory_level,
            "advisory": (
                title
                or "No advisory summary available."
            ),
        }

    return advisory_map


def get_advisory_data_for_destination(destination, advisory_map):
    country_name = (
        destination.get("country")
        or destination.get("country_name")
        or ""
    )

    country_name = country_name.strip().lower()

    if not country_name:
        return get_default_map_data()

    return advisory_map.get(
        country_name,
        get_default_map_data(),
    )

def get_map_data_for_destination(destination, advisory_map):
    """
    Gets mapScore, riskLevel, and condition for one destination.

    This function does NOT call the external advisory API.
    It only reads from the advisory_map that was already fetched when the backend started.
    """

    advisory_data = get_advisory_data_for_destination(destination, advisory_map)

    return {
        "mapScore": advisory_data["mapScore"],
        "riskLevel": advisory_data["riskLevel"],
        "condition": advisory_data["condition"],
        "advisoryLevel": advisory_data["advisoryLevel"],
        "advisory": advisory_data["advisory"],
    }


def get_advisory(destination, advisory_map):
    """
    Gets advisory text for DestinationDashboardPage.

    This replaces the old mock get_advisory(country_code) function.
    It does NOT call the external advisory API.
    It only reads from the advisory_map that was already fetched when the backend started.
    """

    advisory_data = get_advisory_data_for_destination(destination, advisory_map)
    
    return advisory_data.get(
        "advisory",
        "No advisory information is available for this destination yet.",
    )