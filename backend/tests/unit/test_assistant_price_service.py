# TEST: is_fresh()

from datetime import datetime, timedelta, timezone

from app.services.ai_chatbot_service.assistant_price_service import (
    FLIGHT_MAX_AGE,
    is_fresh,
)


def test_is_fresh_returns_true_for_recent_timestamp():
    checked_at = (
        datetime.now(timezone.utc)
        - timedelta(hours=1)
    )

    assert is_fresh(
        checked_at,
        FLIGHT_MAX_AGE,
    ) is True


def test_is_fresh_returns_false_for_old_timestamp():
    checked_at = (
        datetime.now(timezone.utc)
        - timedelta(hours=5)
    )

    assert is_fresh(
        checked_at,
        FLIGHT_MAX_AGE,
    ) is False


def test_is_fresh_returns_false_when_timestamp_missing():
    assert is_fresh(
        None,
        FLIGHT_MAX_AGE,
    ) is False

# TEST: saved-flight matching 

from app.services.ai_chatbot_service.assistant_price_service import (
    find_matching_saved_flight,
)


def test_find_matching_saved_flight():
    saved_flights = [
        {
            "id": 1,
            "origin_code": "SIN",
            "destination_code": "TYO",
            "departure_date": "2026-08-10",
        },
        {
            "id": 2,
            "origin_code": "SIN",
            "destination_code": "BKK",
            "departure_date": "2026-08-10",
        },
    ]

    result = find_matching_saved_flight(
        saved_flights=saved_flights,
        origin="sin",
        destination="tyo",
        departure_date="2026-08-10",
    )

    assert result is not None
    assert result["id"] == 1


def test_find_matching_saved_flight_returns_none():
    saved_flights = [
        {
            "id": 1,
            "origin_code": "SIN",
            "destination_code": "TYO",
            "departure_date": "2026-08-10",
        },
    ]

    result = find_matching_saved_flight(
        saved_flights=saved_flights,
        origin="SIN",
        destination="BKK",
        departure_date="2026-08-10",
    )

    assert result is None

# TEST: saved + fresh flight data

from datetime import datetime, timezone

from app.services.ai_chatbot_service.assistant_price_service import (
    resolve_flight_price_data,
)


def test_resolve_flight_uses_fresh_saved_data(
    mocker,
):
    saved_flight = {
        "id": 10,
        "origin_code": "SIN",
        "destination_code": "TYO",
        "departure_date": "2026-08-10",
        "saved_price": 450,
        "current_price": 420,
        "last_checked_at": datetime.now(
            timezone.utc
        ),
    }

    mock_get_saved = mocker.patch(
        "app.services.ai_chatbot_service."
        "assistant_price_service."
        "get_saved_flights_for_user",
        return_value=[saved_flight],
    )

    mock_refresh = mocker.patch(
        "app.services.ai_chatbot_service."
        "assistant_price_service."
        "refresh_saved_flight_price",
    )

    mock_search = mocker.patch(
        "app.services.ai_chatbot_service."
        "assistant_price_service.search_flights",
    )

    result = resolve_flight_price_data(
        username="testuser",
        origin="SIN",
        destination="TYO",
        departure_date="2026-08-10",
        adults=1,
    )

    assert result["source"] == "saved_database"
    assert result["was_refreshed"] is False
    assert result["is_saved"] is True
    assert result["saved_item"]["id"] == 10

    mock_get_saved.assert_called_once_with(
        username="testuser"
    )
    mock_refresh.assert_not_called()
    mock_search.assert_not_called()

# TEST: saved + stale flight data

from datetime import datetime, timedelta, timezone


def test_resolve_flight_refreshes_stale_saved_data(
    mocker,
):
    stale_flight = {
        "id": 10,
        "origin_code": "SIN",
        "destination_code": "TYO",
        "departure_date": "2026-08-10",
        "saved_price": 450,
        "current_price": 450,
        "last_checked_at": (
            datetime.now(timezone.utc)
            - timedelta(hours=5)
        ),
    }

    refreshed_flight = {
        **stale_flight,
        "current_price": 400,
        "price_status": "price_dropped",
        "last_checked_at": datetime.now(
            timezone.utc
        ),
    }

    mocker.patch(
        "app.services.ai_chatbot_service."
        "assistant_price_service."
        "get_saved_flights_for_user",
        return_value=[stale_flight],
    )

    mock_refresh = mocker.patch(
        "app.services.ai_chatbot_service."
        "assistant_price_service."
        "refresh_saved_flight_price",
        return_value=refreshed_flight,
    )

    mock_search = mocker.patch(
        "app.services.ai_chatbot_service."
        "assistant_price_service.search_flights",
    )

    result = resolve_flight_price_data(
        username="testuser",
        origin="SIN",
        destination="TYO",
        departure_date="2026-08-10",
        adults=1,
    )

    assert result["source"] == "refreshed_saved_item"
    assert result["was_refreshed"] is True
    assert result["saved_item"]["current_price"] == 400

    mock_refresh.assert_called_once_with(
        username="testuser",
        saved_flight_id=10,
    )

    mock_search.assert_not_called()

# TEST: no saved flight

def test_resolve_flight_calls_search_when_no_saved_match(
    mocker,
):
    mocker.patch(
        "app.services.ai_chatbot_service."
        "assistant_price_service."
        "get_saved_flights_for_user",
        return_value=[],
    )

    flight_results = [
        {
            "id": "offer-1",
            "route": "SIN → TYO",
            "price": 420,
            "currency": "SGD",
        }
    ]

    mock_search = mocker.patch(
        "app.services.ai_chatbot_service."
        "assistant_price_service.search_flights",
        return_value=flight_results,
    )

    result = resolve_flight_price_data(
        username="testuser",
        origin="SIN",
        destination="TYO",
        departure_date="2026-08-10",
        adults=1,
    )

    assert result["source"] == "new_search"
    assert result["is_saved"] is False
    assert result["results"] == flight_results

    mock_search.assert_called_once_with(
        origin="SIN",
        destination="TYO",
        departure_date="2026-08-10",
        adults=1,
    )

# TEST: invalid inputs

import pytest

from app.services.ai_chatbot_service.assistant_price_service import (
    resolve_flight_price_data,
)


@pytest.mark.parametrize(
    ("origin", "destination", "departure_date", "adults"),
    [
        ("", "TYO", "2026-08-10", 1),
        ("SIN", "", "2026-08-10", 1),
        ("SIN", "TYO", "", 1),
        ("SIN", "TYO", "2026-08-10", 0),
    ],
)
def test_resolve_flight_rejects_invalid_inputs(
    mocker,
    origin,
    destination,
    departure_date,
    adults,
):
    mocker.patch(
        "app.services.ai_chatbot_service."
        "assistant_price_service."
        "get_saved_flights_for_user",
        return_value=[],
    )

    with pytest.raises(ValueError):
        resolve_flight_price_data(
            username="testuser",
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            adults=adults,
        )