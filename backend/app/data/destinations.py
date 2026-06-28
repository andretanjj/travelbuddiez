import json
from pathlib import Path

"""
JPN: countryCode for Mapbox / backend route
jp: newsCode for WorldNews API
Japan: default city/country name for weather and aliases.
"""

# After debugging, we noticed that taiwan and scarborough reef had unusual iso codes
NEWS_CODE_OVERRIDES = {
    "TWN": "tw",
    "FRA": "fr",
    "NOR": "no",
    "XKX": "xk",
    "SOM": "so",
    "NCY": "cy",

    # Special territories / disputed areas
    "DHK": "",
    "GTB": "cu",
    "BRI": "br",
    "CNA": "cy",
    "SIA": "",
    "BAY": "kz",
    "AKR": "cy",
    "SPI": "",
    "BTW": "",
    "IOT": "",
    "CSI": "au",
    "SPR": "",
    "CLI": "fr",
    "ACA": "au",
    "BNB": "",
    "SER": "",
    "SCR": "",
}


COUNTRY_CODE_OVERRIDES = {
    "Dhekelia Sovereign Base Area": "DHK",
    "Somaliland": "SOM",
    "France": "FRA",
    "Norway": "NOR",
    "Kosovo": "XKX",
    "US Naval Base Guantanamo Bay": "GTB",
    "Brazilian Island": "BRI",
    "Northern Cyprus": "NCY",
    "Cyprus No Mans Area": "CNA",
    "Siachen Glacier": "SIA",
    "Baykonur Cosmodrome": "BAY",
    "Akrotiri Sovereign Base Area": "AKR",
    "Southern Patagonian Ice Field": "SPI",
    "Bir Tawil": "BTW",
    "Indian Ocean Territories": "IOT",
    "Coral Sea Islands": "CSI",
    "Spratly Islands": "SPR",
    "Clipperton Island": "CLI",
    "Ashmore and Cartier Islands": "ACA",
    "Bajo Nuevo Bank (Petrel Is.)": "BNB",
    "Serranilla Bank": "SER",
    "Scarborough Reef": "SCR",
    "Taiwan": "TWN",
}

# Uses the same countries.geojson file structure as the frontend.
COUNTRIES_FILE = Path(__file__).parent / "countries.geojson"


def make_country_code(country_code: str, country_name: str):
    """
    Return a valid 3-character country code.

    Some entries in countries.geojson have ISO3 code "-99".
    Since "-99" is not unique, we manually assign custom 3-character codes.
    """

    if country_code != "-99":
        return country_code

    return COUNTRY_CODE_OVERRIDES.get(country_name)


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

    if not country_code:
        print(f"Missing country code override for: {country_name}")
        continue

    if len(country_code) != 3:
        raise ValueError(f"Invalid country code length for {country_name}: {country_code}")

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