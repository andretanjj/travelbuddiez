import re
import requests
import xml.etree.ElementTree as ET


# Official U.S. Department of State RSS feed for Travel Advisories.
TRAVEL_ADVISORIES_URL = "https://travel.state.gov/_res/rss/TAsTWs.xml"


# Converts U.S. advisory levels into map-friendly data.
# These values are used by MapView for country colouring and tooltip data.
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
    Returns default map data when no advisory is available.

    This prevents the frontend from crashing when a destination
    cannot be matched to an advisory.
    """
    return {
        "mapScore": None,
        "riskLevel": "Unknown",
        "condition": "No advisory data available",
        "advisoryLevel": None,
        "advisory": "No advisory information is available for this destination yet.",
    }


def extract_advisory_level(text: str):
    """
    Extracts advisory level 1-4 from text.

    Example:
    "Afghanistan Travel Advisory - Level 4: Do Not Travel"
    returns 4.
    """
    if not text:
        return None

    match = re.search(r"Level\s*([1-4])", text, re.IGNORECASE)

    if match is None:
        return None

    return int(match.group(1))


def extract_country_name_from_title(title: str):
    """
    Extracts and normalises the country name from an advisory title.

    Examples:
    "Japan Travel Advisory - Level 1: Exercise Normal Precautions"
    -> "japan"

    "Mexico - Level 2: Exercise Increased Caution"
    -> "mexico"
    """
    if not title:
        return None

    country_name = title.strip()

    # Remove everything beginning from " - Level X".
    country_name = re.sub(r"\s*-\s*Level\s*[1-4].*$", "", country_name, flags=re.IGNORECASE)

    # Remove the standard State Department "Travel Advisory" wording.
    country_name = re.sub(r"\s*Travel Advisory\s*$", "", country_name, flags=re.IGNORECASE)

    country_name = country_name.strip().lower()

    if not country_name:
        return None

    return country_name


def fetch_us_travel_advisories():
    """
    Fetches U.S. Department of State Travel Advisories through RSS.

    The RSS feed is parsed into the same advisory_map structure already
    expected by the rest of TravelBuddiez.

    This function does not modify the database directly.
    """
    try:
        response = requests.get(TRAVEL_ADVISORIES_URL, timeout=15)

    except requests.RequestException as error:
        print("US advisory RSS request failed:", error)
        return {}

    if response.status_code != 200:
        print("US advisory RSS error:", response.status_code, response.text[:200])
        return {}

    try:
        root = ET.fromstring(response.content)

    except ET.ParseError as error:
        print("US advisory RSS XML parse error:", error)
        return {}

    advisory_map = {}

    # Standard RSS structure contains multiple <item> entries.
    for item in root.findall(".//item"):
        title_element = item.find("title")
        description_element = item.find("description")

        if title_element is None:
            continue

        title = title_element.text or ""
        description = description_element.text if description_element is not None else ""

        # Some RSS feeds may place the level in the title,
        # while others may include it in the description.
        combined_text = f"{title} {description or ''}"

        country_name = extract_country_name_from_title(title)
        advisory_level = extract_advisory_level(combined_text)

        if country_name is None:
            continue

        if advisory_level is None:
            continue

        map_data = ADVISORY_LEVEL_TO_MAP_DATA.get(advisory_level)

        if map_data is None:
            continue

        advisory_map[country_name] = {
            "mapScore": map_data["mapScore"],
            "riskLevel": map_data["riskLevel"],
            "condition": map_data["condition"],
            "advisoryLevel": advisory_level,
            "advisory": title,
        }

    print("US advisories loaded:", len(advisory_map))

    return advisory_map


def get_advisory_data_for_destination(destination, advisory_map):
    """
    Finds advisory data for one TravelBuddiez destination.

    The database country name is normalised before being matched
    against the RSS advisory map.
    """
    country_name = destination.get("country") or destination.get("country_name") or ""
    country_name = country_name.strip().lower()

    if not country_name:
        return get_default_map_data()

    return advisory_map.get(country_name, get_default_map_data())


def get_map_data_for_destination(destination, advisory_map):
    """
    Gets the map-related advisory data used by MapView.

    This does not make another external API request.
    It reads from the already-created advisory_map.
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

    This uses the same advisory data already fetched for map scores.
    """
    advisory_data = get_advisory_data_for_destination(destination, advisory_map)

    return advisory_data.get(
        "advisory",
        "No advisory information is available for this destination yet.",
    )