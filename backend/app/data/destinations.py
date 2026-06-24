import json
import re
from pathlib import Path

"""
JPN: countryCode for Mapbox / backend route
jp: newsCode for WorldNews API
Japan: default city/country name for weather and aliases.
"""

# After debugging, we noticed that taiwan and scarborough reef had unusual iso codes
NEWS_CODE_OVERRIDES = {
    "TWN": "tw",
    "FRANCE": "fr",
    "NORWAY": "no",
    "KOSOVO": "xk",
    "SOMALILAND": "so",
    "NORTHERN_CYPRUS": "cy",
}

# Uses the same countries.geojson file structure as the frontend.
COUNTRIES_FILE = Path(__file__).parent / "countries.geojson"


def make_country_code(country_code: str, country_name: str):
    """
    Some countries in countries.geojson have ISO3 code "-99".
    Since "-99" is not unique, generate a unique code from the country name.
    """

    if country_code != "-99":
        return country_code

    generated_code = country_name.upper()
    generated_code = re.sub(r"[^A-Z0-9]+", "_", generated_code)
    generated_code = generated_code.strip("_")

    return generated_code


def get_news_code(country_code: str, country_code_iso2: str):
    if country_code in NEWS_CODE_OVERRIDES:
        return NEWS_CODE_OVERRIDES[country_code]

    if country_code_iso2 == "-99":
        return ""

    return country_code_iso2.lower()


def load_geojson_countries():
    """
    Loads country polygon and property data from countries.geojson.
    """

    with open(COUNTRIES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def load_capital_overrides():
    try:
        response = requests.get(REST_COUNTRIES_URL, timeout=10)
        response.raise_for_status()

        countries = response.json()

        if not isinstance(countries, list):
            print("Unexpected Rest Countries response:", countries)
            return {}

        city_overrides = {}

        for country in countries:
            if not isinstance(country, dict):
                continue

            country_code = country.get("cca3")
            capitals = country.get("capital", [])

            if not country_code:
                continue

            if capitals:
                city_overrides[country_code] = capitals[0]

        return city_overrides

    except Exception as error:
        print("Failed to load capital overrides:", error)
        return {}


CITY_OVERRIDES = load_capital_overrides()

countries_geojson = load_geojson_countries()

DESTINATIONS = {}

for feature in countries_geojson["features"]:
    properties = feature.get("properties", {})

    raw_country_code = properties.get("ISO3166-1-Alpha-3")
    country_name = properties.get("name")
    country_code_iso2 = properties.get("ISO3166-1-Alpha-2")

    if not raw_country_code or not country_name or not country_code_iso2:
        continue

    country_code = make_country_code(raw_country_code, country_name)
    news_code = get_news_code(country_code, country_code_iso2)

    DESTINATIONS[country_code] = {
        "countryCode": country_code,
        "country": country_name,

        # Use country name as the default city for now.
        # Later, this can be replaced by a database column or manual capital-city mapping.
        "city": country_name,

        # World News API uses ISO2 country code.
        "newsCode": news_code,
    }