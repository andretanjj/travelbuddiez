from app.services.travel_planning_service import (
    search_flights,
    search_hotels,
)


def test_search_flights_returns_duffel_results(
    mocker,
):
    expected = [
        {
            "id": "offer-1",
            "price": 420,
        }
    ]

    mocker.patch(
        "app.services.travel_planning_service."
        "search_duffel_flights",
        return_value=expected,
    )

    result = search_flights(
        origin="SIN",
        destination="TYO",
        departure_date="2026-08-10",
        adults=1,
    )

    assert result == expected


def test_search_flights_falls_back_when_duffel_fails(
    mocker,
):
    mocker.patch(
        "app.services.travel_planning_service."
        "search_duffel_flights",
        side_effect=RuntimeError("Duffel unavailable"),
    )

    result = search_flights(
        origin="SIN",
        destination="NRT",
        departure_date="2026-08-10",
        adults=1,
    )

    assert isinstance(result, list)
    assert len(result) > 0
    assert result[0]["route"] == "SIN → NRT"


def test_search_hotels_returns_liteapi_results(
    mocker,
):
    expected = [
        {
            "id": "hotel-live-1",
            "name": "Tokyo Central Hotel",
            "city": "Tokyo",
            "country": "Japan",
            "price": 210,
            "currency": "USD",
            "rating": 8.8,
            "checkInDate": "2026-08-10",
            "checkOutDate": "2026-08-13",
        }
    ]

    mock_liteapi = mocker.patch(
        "app.services.travel_planning_service."
        "search_liteapi_hotels",
        return_value=expected,
    )

    result = search_hotels(
        city="TYO",
        check_in_date="2026-08-10",
        check_out_date="2026-08-13",
        adults=1,
    )

    assert result == expected

    mock_liteapi.assert_called_once_with(
        city="TYO",
        check_in_date="2026-08-10",
        check_out_date="2026-08-13",
        adults=1,
    )


def test_search_hotels_falls_back_when_liteapi_fails(
    mocker,
):
    mocker.patch(
        "app.services.travel_planning_service."
        "search_liteapi_hotels",
        side_effect=RuntimeError("LiteAPI unavailable"),
    )

    result = search_hotels(
        city="Tokyo",
        check_in_date="2026-08-10",
        check_out_date="2026-08-13",
        adults=1,
    )

    assert isinstance(result, list)
    assert len(result) > 0
    assert result[0]["name"] == "Tokyo Bay Hotel"
    assert result[0]["city"] == "Tokyo"
    assert result[0]["checkInDate"] == "2026-08-10"
    assert result[0]["checkOutDate"] == "2026-08-13"

def test_search_hotels_fallback_is_sorted_by_price(
    mocker,
):
    mocker.patch(
        "app.services.travel_planning_service."
        "search_liteapi_hotels",
        side_effect=RuntimeError("LiteAPI unavailable"),
    )

    result = search_hotels(
        city="Tokyo",
        check_in_date="2026-08-10",
        check_out_date="2026-08-13",
        adults=1,
    )

    prices = [
        hotel["price"]
        for hotel in result
    ]

    assert prices == sorted(prices)