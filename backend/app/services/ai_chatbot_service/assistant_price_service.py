from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.services.saved_travel_service import (
    get_saved_flights_for_user,
    get_saved_hotels_for_user,
    refresh_saved_flight_price,
    refresh_saved_hotel_price,
)
from app.services.travel_planning_service import (
    search_flights,
    search_hotels,
)

FLIGHT_MAX_AGE = timedelta(hours=3)
HOTEL_MAX_AGE = timedelta(hours=6)

def is_fresh(
    last_checked_at: datetime | None,
    max_age: timedelta,
) -> bool:
    """
    Checks whether a previously refreshed price is still recent enough.
    """

    if last_checked_at is None:
        return False

    checked_at = last_checked_at

    if checked_at.tzinfo is None:
        checked_at = checked_at.replace(
            tzinfo=timezone.utc,
        )

    return (
        datetime.now(timezone.utc) - checked_at
        <= max_age
    )


def normalise_date(value: Any) -> str:
    """
    Converts a date, datetime or string into YYYY-MM-DD format.
    """

    if isinstance(value, datetime):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    return str(value or "").strip()


def find_matching_saved_flight(
    saved_flights: list[dict[str, Any]],
    origin: str,
    destination: str,
    departure_date: str,
) -> dict[str, Any] | None:
    """
    Finds a saved flight with the same origin, destination and
    departure date.
    """

    requested_origin = origin.strip().upper()
    requested_destination = destination.strip().upper()
    requested_date = normalise_date(departure_date)

    for flight in saved_flights:
        saved_origin = str(
            flight.get("origin_code")
            or flight.get("origin")
            or ""
        ).strip().upper()

        saved_destination = str(
            flight.get("destination_code")
            or flight.get("destination")
            or ""
        ).strip().upper()

        saved_departure_date = normalise_date(
            flight.get("departure_date")
        )

        if (
            saved_origin == requested_origin
            and saved_destination == requested_destination
            and saved_departure_date == requested_date
        ):
            return flight

    return None


def resolve_flight_price_data(
    username: str,
    origin: str,
    destination: str,
    departure_date: str,
    adults: int,
) -> dict[str, Any]:
    """
    Uses saved database data first.

    Flow:
    1. Find a matching saved flight.
    2. Use it if its checked price is still fresh.
    3. Refresh it if its checked price is stale.
    4. Perform a new search if no matching saved flight exists.
    """

    origin = origin.strip().upper()
    destination = destination.strip().upper()
    departure_date = normalise_date(departure_date)

    if not origin:
        raise ValueError("Flight origin is required.")

    if not destination:
        raise ValueError("Flight destination is required.")

    if not departure_date:
        raise ValueError("Flight departure date is required.")

    if adults < 1:
        raise ValueError(
            "The number of adult passengers must be at least 1."
        )

    saved_flights = get_saved_flights_for_user(
        username=username,
    )

    saved_flight = find_matching_saved_flight(
        saved_flights=saved_flights,
        origin=origin,
        destination=destination,
        departure_date=departure_date,
    )

    # Matching saved flight exists.
    if saved_flight is not None:
        # Use database data if it was refreshed recently.
        if is_fresh(
            saved_flight.get("last_checked_at"),
            FLIGHT_MAX_AGE,
        ):
            return {
                "source": "saved_database",
                "was_refreshed": False,
                "is_saved": True,
                "saved_item": saved_flight,
                "results": [saved_flight],
                "message": (
                    "A recently checked matching saved flight was found."
                ),
            }

        # Saved data exists but is stale, so refresh it.
        refreshed_flight = refresh_saved_flight_price(
            username=username,
            saved_flight_id=saved_flight["id"],
        )

        return {
            "source": "refreshed_saved_item",
            "was_refreshed": True,
            "is_saved": True,
            "saved_item": refreshed_flight,
            "results": [refreshed_flight],
            "message": (
                "The matching saved flight price was outdated, "
                "so it was refreshed."
            ),
        }

    # No matching saved flight exists, so perform a new search.
    search_results = search_flights(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        adults=adults,
    )

    return {
        "source": "new_search",
        "was_refreshed": False,
        "is_saved": False,
        "saved_item": None,
        "results": search_results,
        "message": (
            "No matching saved flight was found, so a new flight "
            "search was performed."
        ),
    }

def find_matching_saved_hotel(
    saved_hotels: list[dict[str, Any]],
    destination: str,
    check_in_date: str,
    check_out_date: str,
) -> dict[str, Any] | None:
    """
    Finds a saved hotel with the same destination and stay dates.
    """

    requested_destination = destination.strip().upper()
    requested_check_in = normalise_date(check_in_date)
    requested_check_out = normalise_date(check_out_date)

    for hotel in saved_hotels:
        saved_destination = str(
            hotel.get("destination_code")
            or hotel.get("destination")
            or hotel.get("city")
            or ""
        ).strip().upper()

        saved_check_in = normalise_date(
            hotel.get("check_in_date")
            or hotel.get("checkInDate")
        )

        saved_check_out = normalise_date(
            hotel.get("check_out_date")
            or hotel.get("checkOutDate")
        )

        if (
            saved_destination == requested_destination
            and saved_check_in == requested_check_in
            and saved_check_out == requested_check_out
        ):
            return hotel

    return None


def resolve_hotel_price_data(
    username: str,
    destination: str,
    check_in_date: str,
    check_out_date: str,
    adults: int,
) -> dict[str, Any]:
    """
    Uses saved hotel data first.

    Flow:
    1. Find a matching saved hotel.
    2. Use it if its checked price is still fresh.
    3. Refresh it if its checked price is stale.
    4. Perform a new search if no matching saved hotel exists.
    """

    destination = destination.strip().upper()
    check_in_date = normalise_date(check_in_date)
    check_out_date = normalise_date(check_out_date)

    if not destination:
        raise ValueError("Hotel destination is required.")

    if not check_in_date:
        raise ValueError("Hotel check-in date is required.")

    if not check_out_date:
        raise ValueError("Hotel check-out date is required.")

    if check_out_date <= check_in_date:
        raise ValueError(
            "Hotel check-out date must be after check-in date."
        )

    if adults < 1:
        raise ValueError(
            "The number of adult guests must be at least 1."
        )

    saved_hotels = get_saved_hotels_for_user(
        username=username,
    )

    saved_hotel = find_matching_saved_hotel(
        saved_hotels=saved_hotels,
        destination=destination,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
    )

    # Matching saved hotel exists.
    if saved_hotel is not None:
        # Use database data when the checked price is still fresh.
        if is_fresh(
            saved_hotel.get("last_checked_at"),
            HOTEL_MAX_AGE,
        ):
            return {
                "source": "saved_database",
                "was_refreshed": False,
                "is_saved": True,
                "saved_item": saved_hotel,
                "results": [saved_hotel],
                "message": (
                    "A recently checked matching saved hotel was found."
                ),
            }

        # Saved hotel exists, but the price data is stale.
        refreshed_hotel = refresh_saved_hotel_price(
            username=username,
            saved_hotel_id=saved_hotel["id"],
        )

        return {
            "source": "refreshed_saved_item",
            "was_refreshed": True,
            "is_saved": True,
            "saved_item": refreshed_hotel,
            "results": [refreshed_hotel],
            "message": (
                "The matching saved hotel price was outdated, "
                "so it was refreshed."
            ),
        }

    # No matching saved hotel exists, so perform a new search.
    search_results = search_hotels(
        city=destination,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        adults=adults,
    )

    return {
        "source": "new_search",
        "was_refreshed": False,
        "is_saved": False,
        "saved_item": None,
        "results": search_results,
        "message": (
            "No matching saved hotel was found, so a new hotel "
            "search was performed."
        ),
    }