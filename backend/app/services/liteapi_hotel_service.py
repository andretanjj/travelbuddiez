import logging
import os
import requests

logger = logging.getLogger("uvicorn.error")


LITEAPI_API_KEY = os.getenv("LITEAPI_API_KEY")
LITEAPI_BASE_URL = os.getenv("LITEAPI_BASE_URL", "https://api.liteapi.travel/v3.0")


def get_liteapi_headers():
    """
    Builds headers for LiteAPI requests.

    Keep the API key in the backend only.
    Never expose this key in the Vite frontend.
    """

    return {
        "X-API-Key": LITEAPI_API_KEY,
        "Content-Type": "application/json",
    }


def get_hotel_price_and_currency(hotel_rate):
    """
    Extracts the cheapest available rate from one LiteAPI hotel rate result.

    The /hotels/rates response contains:
    - hotelId
    - roomTypes
    - rates
    - retailRate.total
    """

    price = 0
    currency = "USD"

    room_types = hotel_rate.get("roomTypes", [])

    if len(room_types) == 0:
        return price, currency

    first_room_type = room_types[0]
    rates = first_room_type.get("rates", [])

    if len(rates) == 0:
        return price, currency

    first_rate = rates[0]
    retail_rate = first_rate.get("retailRate", {})
    total_prices = retail_rate.get("total", [])

    if len(total_prices) == 0:
        return price, currency

    price = float(total_prices[0].get("amount", 0))
    currency = total_prices[0].get("currency", "USD")

    return price, currency


def fetch_liteapi_hotel_details(hotel_id: str):
    """
    Fetches full hotel metadata from LiteAPI /data/hotel.

    This gives real hotel name, city, country, address, rating, images, etc.
    If the metadata call fails, return None so the caller can use fallback labels.
    """

    url = f"{LITEAPI_BASE_URL}/data/hotel"

    response = requests.get(
        url,
        headers=get_liteapi_headers(),
        params={"hotelId": hotel_id},
        timeout=20,
    )

    if not response.ok:
        logger.warning(
            "[LITEAPI] Hotel metadata request failed for hotel %s "
            "with status %s. Using fallback hotel labels.",
            hotel_id,
            response.status_code,
        )

        return None

    response_data = response.json()

    # LiteAPI may return either {"data": {...}} or the hotel object directly.
    return response_data.get("data") or response_data


def normalise_liteapi_hotel(hotel_rate, hotel_details, check_in_date: str, check_out_date: str):
    """
    Merges LiteAPI rate data with hotel metadata.

    Rate data provides:
    - hotelId
    - price
    - currency

    Hotel metadata provides:
    - name
    - city
    - country
    - star rating
    """

    hotel_id = hotel_rate.get("hotelId", "unknown-hotel")
    price, currency = get_hotel_price_and_currency(hotel_rate)

    # Metadata fallback values.
    hotel_name = f"Hotel {hotel_id}"
    city = "Selected destination"
    country = "Available via LiteAPI"
    rating = 0

    if hotel_details is not None:
        # Use safe .get() calls because provider fields can vary.
        hotel_name = (
            hotel_details.get("name")
            or hotel_details.get("hotelName")
            or hotel_name
        )

        city = (
            hotel_details.get("city")
            or hotel_details.get("cityName")
            or hotel_details.get("address", {}).get("city")
            or city
        )

        country = (
            hotel_details.get("country")
            or hotel_details.get("countryCode")
            or hotel_details.get("address", {}).get("country")
            or country
        )

        rating = float(
            hotel_details.get("rating")
            or hotel_details.get("starRating")
            or hotel_details.get("stars")
            or 0
        )

    return {
        "id": str(hotel_id),
        "name": hotel_name,
        "city": city,
        "country": country,
        "price": price,
        "currency": currency,
        "rating": rating,
        "checkInDate": check_in_date,
        "checkOutDate": check_out_date,
    }


def search_liteapi_hotels(city: str, check_in_date: str, check_out_date: str, adults: int):
    """
    Searches LiteAPI hotels.

    Flow:
    1. Call /hotels/rates to get bookable hotel IDs and real prices.
    2. Call /data/hotel for each hotelId to get real names/details.
    3. Merge price + metadata into the frontend HotelResult shape.
    """

    if not LITEAPI_API_KEY:
        raise RuntimeError("LITEAPI_API_KEY is missing")

    logger.info(
        "[LITEAPI] Calling live hotel rates API: destination=%s, "
        "check-in=%s, check-out=%s, adults=%s",
        city.upper(),
        check_in_date,
        check_out_date,
        adults,
    )

    rates_url = f"{LITEAPI_BASE_URL}/hotels/rates"

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
        # For now, the frontend hotel destination input should contain codes like TYO or SIN.
        "iataCode": city.upper(),

        # Keep results small for faster demo and lower API usage.
        "limit": 10,
        "timeout": 10,
        "maxRatesPerHotel": 1,
    }

    rates_response = requests.post(
        rates_url,
        headers=get_liteapi_headers(),
        json=payload,
        timeout=20,
    )

    logger.info(
        "[LITEAPI] Hotel rates HTTP response received with status %s",
        rates_response.status_code,
    )

    if not rates_response.ok:
        logger.error(
            "[LITEAPI] Live hotel rates request failed with status %s",
            rates_response.status_code,
        )

        raise RuntimeError(
            f"LiteAPI hotel rates request failed: "
            f"{rates_response.status_code} {rates_response.text}"
        )

    rates_data = rates_response.json()

    hotel_rates = (
        rates_data.get("data")
        or rates_data.get("hotels")
        or rates_data.get("results")
        or []
    )

    logger.info(
        "[LITEAPI] Live API returned %s hotel rate result(s)",
        len(hotel_rates),
    )

    normalised_hotels = []

    for hotel_rate in hotel_rates[:10]:
        hotel_id = hotel_rate.get("hotelId")

        hotel_details = None

        if hotel_id:
            logger.info(
            "[LITEAPI] Fetching live metadata for hotel %s",
            hotel_id,
        )
            hotel_details = fetch_liteapi_hotel_details(
                str(hotel_id)
            )

        normalised_hotel = normalise_liteapi_hotel(
            hotel_rate=hotel_rate,
            hotel_details=hotel_details,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
        )

        # Do not include missing or zero-value prices.
        if normalised_hotel["price"] > 0:
            normalised_hotels.append(
                normalised_hotel
            )

    sorted_hotels = sorted(normalised_hotels, key=lambda hotel: hotel["price"])

    logger.info(
        "[LITEAPI] Successfully normalised %s live hotel result(s)",
        len(sorted_hotels),
    )

    return sorted_hotels