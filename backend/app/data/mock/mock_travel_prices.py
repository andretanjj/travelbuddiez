MOCK_PRICES = {
    "JPN": {
        "flight_price": 650,
        "hotel_price": 750,
        "currency": "SGD",
        "price_source": "mock",
    },
    "THA": {
        "flight_price": 210,
        "hotel_price": 320,
        "currency": "SGD",
        "price_source": "mock",
    },
    "MYS": {
        "flight_price": 140,
        "hotel_price": 260,
        "currency": "SGD",
        "price_source": "mock",
    },
    "KOR": {
        "flight_price": 520,
        "hotel_price": 570,
        "currency": "SGD",
        "price_source": "mock",
    },
    "TWN": {
        "flight_price": 390,
        "hotel_price": 460,
        "currency": "SGD",
        "price_source": "mock",
    },
}


def add_mock_prices(
    destination_data: list[dict],
) -> list[dict]:
    enriched_destinations: list[dict] = []

    for destination in destination_data:
        enriched_destination = destination.copy()

        country_code = destination.get("country_code")
        mock_price = MOCK_PRICES.get(country_code)

        if mock_price:
            enriched_destination.update(mock_price)

            enriched_destination["estimated_total_price"] = (
                mock_price["flight_price"]
                + mock_price["hotel_price"]
            )

        enriched_destinations.append(enriched_destination)

    return enriched_destinations