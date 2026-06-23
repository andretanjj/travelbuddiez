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


def load_capital_overrides():
    response = requests.get(REST_COUNTRIES_URL, timeout=10)
    response.raise_for_status()

    countries = response.json()

    if not isinstance(countries, list):
            print("REST Countries returned unexpected data:", countries)
            return {}
            
    city_overrides = {}

    for country in countries:
        country_code = country.get("cca3")
        capitals = country.get("capital", [])

        if not country_code:
            continue

        if capitals:
            city_overrides[country_code] = capitals[0]

    return city_overrides


CITY_OVERRIDES = load_capital_overrides()

countries_geojson = load_geojson_countries()

DESTINATIONS = {}

for feature in countries_geojson["features"]:
    properties = feature.get("properties", {})

    country_code = properties.get("ISO3166-1-Alpha-3")
    country_name = properties.get("name")
    country_code_iso2 = properties.get("ISO3166-1-Alpha-2", "").lower() #this is for worldnewsAPI as it uses ISO2 country code

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