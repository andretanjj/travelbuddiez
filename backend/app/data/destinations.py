import json
import requests
from pathlib import Path

COUNTRIES_FILE = Path(__file__).parent / "countries.geojson" #uses the same file in frtonend

REST_COUNTRIES_URL = "https://restcountries.com/v3.1/all?fields=name,cca3,capital" #get all capital cities


def load_geojson_countries():
    with open(COUNTRIES_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def load_capital_overrides():
    response = requests.get(REST_COUNTRIES_URL)
    response.raise_for_status()

    countries = response.json()
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
    country_code_iso2 = properties.get("ISO3166-1-Alpha-2").lower() #this is for worldnewsAPI as it uses ISO2 country code

    if not country_code or not country_name:
        continue

    DESTINATIONS[country_code] = {
        "countryCode": country_code,
        "country": country_name,
        "city": CITY_OVERRIDES.get(country_code, country_name),
        "newsCode": country_code_iso2,
    }