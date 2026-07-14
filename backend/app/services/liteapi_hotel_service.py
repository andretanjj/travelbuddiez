import os
import requests


LITEAPI_API_KEY = os.getenv("LITEAPI_API_KEY")
LITEAPI_BASE_URL = os.getenv("LITEAPI_BASE_URL", "https://api.liteapi.travel/v3.0")


def normalise_liteapi_hotel(hotel_rate, check_in_date: str, check_out_date: str):
    """
    Converts one LiteAPI hotel rate result into the simplified HotelResult shape
    used by the frontend.

    LiteAPI /hotels/rates gives hotelId and pricing data.
    Hotel name/city/country are not always included here, so we use safe fallback labels.
    Later, we can call /data/hotels to enrich this with full hotel metadata.
    """

    hotel_id = hotel_rate.get("hotelId", "unknown-hotel")

    # Default fallback values.
    price = 0
    currency = "USD"
    rating = 0

    room_types = hotel_rate.get("roomTypes", [])

    if len(room_types) > 0:
        first_room_type = room_types[0]
        rates = first_room_type.get("rates", [])

        if len(rates) > 0:
            first_rate = rates[0]
            retail_rate = first_rate.get("retailRate", {})
            total_prices = retail_rate.get("total", [])

            if len(total_prices) > 0:
                price = float(total_prices[0].get("amount", 0))
                currency = total_prices[0].get("currency", "USD")

    return {
        "id": str(hotel_id),

        # Temporary display until we add /data/hotels metadata enrichment.
        "name": f"Hotel {hotel_id}",
        "city": "Selected destination",
        "country": "Available via LiteAPI",

        "price": price,
        "currency": currency,
        "rating": rating,
        "checkInDate": check_in_date,
        "checkOutDate": check_out_date,
    }


def search_liteapi_hotels(city: str, check_in_date: str, check_out_date: str, adults: int):
    """
    Calls LiteAPI hotel rates endpoint.

    Current:
    - Searches by cityName using natural city input from the frontend.
    - Uses Singapore as guest nationality for the current TravelBuddiez user base.
    - Returns cheapest available hotels first.

    Later:
    - Replace city text input with LiteAPI Places autocomplete and pass placeId.
    """

    if not LITEAPI_API_KEY:
        raise RuntimeError("LITEAPI_API_KEY is missing")

    url = f"{LITEAPI_BASE_URL}/hotels/rates"

    headers = {
        # LiteAPI dashboard/API reference uses an API key credential in request headers.
        # Keep this server-side only; never expose it in the Vite frontend.
        "X-API-Key": LITEAPI_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "checkin": check_in_date,
        "checkout": check_out_date,
        "currency": "USD",
        "guestNationality": "SG",
        "occupancies": [
            {
                "adults": adults,
            }
        ],

        # LiteAPI rates endpoint accepts iataCode as one valid search method.
        # For now, the frontend city input should contain an IATA city/airport code,
        # for example TYO, HND, NRT, SIN, or KUL.
        "iataCode": city.upper(),

        # Keep results small for faster MS2 demo and cheaper API usage.
        "limit": 10,
        "timeout": 10,
        "maxRatesPerHotel": 1,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=20)

    if not response.ok:
        raise RuntimeError(f"LiteAPI hotel request failed: {response.status_code} {response.text}")

    response_data = response.json()

    # LiteAPI responses may store hotel rates under different top-level keys.
    hotel_rates = (
        response_data.get("data")
        or response_data.get("hotels")
        or response_data.get("results")
        or []
    )

    normalised_hotels = []

    for hotel_rate in hotel_rates[:10]:
        normalised_hotels.append(
            normalise_liteapi_hotel(
                hotel_rate=hotel_rate,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
            )
        )

    return sorted(normalised_hotels, key=lambda hotel: hotel["price"])