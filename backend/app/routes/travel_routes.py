import logging

from fastapi import APIRouter, HTTPException, Query

from app.services.travel_planning_service import search_flights, search_hotels

from app.services.travel_place_service import search_travel_places

from app.services.currency_service import get_exchange_rate

logger = logging.getLogger("uvicorn.error")

router = APIRouter(
    prefix="/travel",
    tags=["travel planning"],
)


@router.get("/flights/search")
def get_flight_results(
    origin: str = Query(..., description="Origin airport code, e.g. SIN"),
    destination: str = Query(
        ...,
        description="Destination airport/city code, e.g. NRT or Tokyo",
    ),
    departure_date: str = Query(
        ...,
        alias="departureDate",
        description="Departure date in YYYY-MM-DD format",
    ),
    return_date: str | None = Query(
        None,
        alias="returnDate",
        description=(
            "Optional return date in YYYY-MM-DD format. "
            "If omitted, the search is one-way."
        ),
    ),
    adults: int = Query(
        1,
        ge=1,
        description="Number of adult passengers",
    ),
):
    """
    Searches flights through the travel-planning service.
    """

    logger.info(
        "[FLIGHT SEARCH] Request received: %s → %s, date=%s, adults=%s",
        origin.upper(),
        destination.upper(),
        departure_date,
        adults,
    )

    flights = search_flights(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        adults=adults,
    )

    logger.info(
        "[FLIGHT SEARCH] Request received: %s → %s, "
        "departure=%s, return=%s, adults=%s",
        origin.upper(),
        destination.upper(),
        departure_date,
        return_date,
        adults,
    )

    return {
        "results": flights,
    }


@router.get("/hotels/search")
def get_hotel_results(
    city: str = Query(..., description="Destination city or IATA code"),
    check_in_date: str = Query(
        ...,
        alias="checkInDate",
        description="Check-in date in YYYY-MM-DD format",
    ),
    check_out_date: str = Query(
        ...,
        alias="checkOutDate",
        description="Check-out date in YYYY-MM-DD format",
    ),
    adults: int = Query(
        1,
        ge=1,
        description="Number of adult guests",
    ),
):
    """
    Searches hotels through the travel-planning service.
    """

    logger.info(
        "[HOTEL SEARCH] Request received: destination=%s, "
        "check-in=%s, check-out=%s, adults=%s",
        city.upper(),
        check_in_date,
        check_out_date,
        adults,
    )

    hotels = search_hotels(
        city=city,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        adults=adults,
    )

    logger.info(
        "[HOTEL SEARCH] Returning %s hotel result(s) to frontend",
        len(hotels),
    )

    return {
        "results": hotels,
    }


@router.get("/places")
def get_travel_place_suggestions(
    query: str = Query(..., min_length=2, description="Search text, e.g. Sing or Tokyo"),
    mode: str = Query("flight", description="Autocomplete mode: flight or hotel"),
):
    """
    Returns Trip.com-style travel suggestions for autocomplete.

    mode=flight:
    - Prefer cities and airports.

    mode=hotel:
    - Prefer cities, areas, stations, and landmarks.
    """

    return {
        "results": search_travel_places(query=query, mode=mode),
    }


@router.get("/currency/rate")
def get_currency_rate(
    from_currency: str = Query(
        ...,
        alias="from",
        min_length=3,
        max_length=3,
        description="Source currency code, e.g. USD",
    ),
    to_currency: str = Query(
        ...,
        alias="to",
        min_length=3,
        max_length=3,
        description="Target currency code, e.g. SGD",
    ),
):
    """
    Returns the latest exchange rate used for display conversion.

    The original Duffel/LiteAPI prices are never changed.
    """

    try:
        return get_exchange_rate(
            from_currency=from_currency,
            to_currency=to_currency,
        )

    except ValueError as error:
        # Unsupported user input.
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except RuntimeError as error:
        # Frankfurter request failed.
        raise HTTPException(
            status_code=502,
            detail=str(error),
        )