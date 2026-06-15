import json
from pathlib import Path


# Uses the same countries.geojson file structure as the frontend.
COUNTRIES_FILE = Path(__file__).parent / "countries.geojson"


def load_geojson_countries():
    """
    Loads country polygon and property data from countries.geojson.
    """

    with open(COUNTRIES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


countries_geojson = load_geojson_countries()

DESTINATIONS = {}

for feature in countries_geojson["features"]:
    properties = feature.get("properties", {})

    country_code = properties.get("ISO3166-1-Alpha-3")
    country_name = properties.get("name")
    country_code_iso2 = properties.get("ISO3166-1-Alpha-2")

    if not country_code or not country_name or not country_code_iso2:
        continue

    DESTINATIONS[country_code] = {
        "countryCode": country_code,
        "country": country_name,

        # Use country name as the default city for now.
        # Later, this can be replaced by a database column or manual capital-city mapping.
        "city": country_name,

        # World News API uses ISO2 country code.
        "newsCode": country_code_iso2.lower(),
    }