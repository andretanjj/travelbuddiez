import logging

from app.services.duffel_flight_service import search_duffel_flights
from app.services.liteapi_hotel_service import search_liteapi_hotels

logger = logging.getLogger("uvicorn.error")

"""
Temp backend mock service for travel planning.
- Let frontend call FastAPI instead of local mock data
- Keep responsen shape close to what Duffel / LiteAPI will return later.
- Fallback data if APIs are unavail.
"""

def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    adults: int,
    return_date: str | None = None,
):
    """
    Tries the live Duffel API first.

    Mock data is returned only when the live provider raises an error.
    """

    logger.info(
        "[FLIGHT SEARCH] Attempting live Duffel search for %s → %s",
        origin.upper(),
        destination.upper(),
    )

    try:
        live_flights = search_duffel_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            adults=adults,
        )

        logger.info(
            "[FLIGHT SEARCH] Live Duffel search succeeded. "
            "Using %s live result(s); mock fallback was not used.",
            len(live_flights),
        )

        return live_flights

    except Exception as error:
        logger.exception(
            "[FLIGHT SEARCH] Duffel search failed: %s. "
            "Proceeding to mock fallback data.",
            error,
        )

    mock_flights = [
        {
            "id": "flight-1",
            "city": "Tokyo",
            "country": "Japan",
            "route": "SIN → NRT",
            "price": 420,
            "currency": "SGD",
            "airline": "Scoot",
            "duration": "6h 50m",
            "stops": "Direct",
            "departureDate": departure_date,
        },
        {
            "id": "flight-2",
            "city": "Seoul",
            "country": "South Korea",
            "route": "SIN → ICN",
            "price": 390,
            "currency": "SGD",
            "airline": "Korean Air",
            "duration": "6h 20m",
            "stops": "Direct",
            "departureDate": departure_date,
        },
    ]

    filtered_flights = []

    for flight in mock_flights:
        route_text = flight["route"].lower()
        city_text = flight["city"].lower()
        country_text = flight["country"].lower()

        if (
            origin.lower() in route_text
            and (
                destination.lower() in route_text
                or destination.lower() in city_text
                or destination.lower() in country_text
            )
        ):
            filtered_flights.append(flight)

    fallback_results = sorted(
        filtered_flights,
        key=lambda flight: flight["price"],
    )

    logger.warning(
        "[FLIGHT SEARCH] Returning %s mock fallback flight result(s)",
        len(fallback_results),
    )

    return fallback_results


def search_hotels(
    city: str,
    check_in_date: str,
    check_out_date: str,
    adults: int,
):
    """
    Tries the live LiteAPI service first.

    Mock data is returned only when the live provider raises an error.
    """

    logger.info(
        "[HOTEL SEARCH] Attempting live LiteAPI search for %s",
        city.upper(),
    )

    try:
        live_hotels = search_liteapi_hotels(
            city=city,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            adults=adults,
        )

        logger.info(
            "[HOTEL SEARCH] Live LiteAPI search succeeded. "
            "Using %s live result(s); mock fallback was not used.",
            len(live_hotels),
        )

        return live_hotels

    except Exception as error:
        logger.exception(
            "[HOTEL SEARCH] LiteAPI search failed: %s. "
            "Proceeding to mock fallback data.",
            error,
        )

    mock_hotels = [
        {
            "id": "hotel-1",
            "name": "Tokyo Bay Hotel",
            "city": "Tokyo",
            "country": "Japan",
            "price": 180,
            "currency": "SGD",
            "rating": 9.1,
            "checkInDate": check_in_date,
            "checkOutDate": check_out_date,
        },
        {
            "id": "hotel-2",
            "name": "Seoul Central Stay",
            "city": "Seoul",
            "country": "South Korea",
            "price": 160,
            "currency": "SGD",
            "rating": 9.0,
            "checkInDate": check_in_date,
            "checkOutDate": check_out_date,
        },
    ]

    filtered_hotels = []

    for hotel in mock_hotels:
        search_text = (
            f"{hotel['name']} {hotel['city']} {hotel['country']}"
        ).lower()

        if city.lower() in search_text:
            filtered_hotels.append(hotel)

    fallback_results = sorted(
        filtered_hotels,
        key=lambda hotel: hotel["price"],
    )

    logger.warning(
        "[HOTEL SEARCH] Returning %s mock fallback hotel result(s)",
        len(fallback_results),
    )

    return fallback_results

