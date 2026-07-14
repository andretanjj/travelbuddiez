from app.services.duffel_flight_service import search_duffel_flights

"""
Temp backend mock service for travel planning.
- Let frontend call FastAPI instead of local mock data
- Keep responsen shape close to what Duffel / LiteAPI will return later.
- Fallback data if APIs are unavail.
"""

def search_flights(origin: str, destination: str, departure_date: str, adults: int):
    """
    Searches flights for the Travel Planning page.

    Current:
    - Tries Duffel first.
    - Falls back to backend mock data if Duffel fails.

    This keeps the Orbital demo reliable even if the external API is down.
    """

    try:
        return search_duffel_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            adults=adults,
        )
    except Exception as error:
        # Fallback is intentional for demo use.
        # This also helps during development if Duffel token/config is wrong.
        print("Duffel flight search failed. Falling back to mock data:", error)

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

    return sorted(filtered_flights, key=lambda flight: flight["price"])

def search_hotels(city: str, check_in_date: str, check_out_date: str, adults: int):
    """
    Returns mock hotel results from backend
    Later:
     - Replace logic with LiteAPI hotel search.
     - Keep returned field names stable for frontend.
    """
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
        search_text = f"{hotel['name']} {hotel['city']} {hotel['country']}".lower()

        if city.lower() in search_text:
            filtered_hotels.append(hotel)

    # Return cheapest first.
    return sorted(filtered_hotels, key=lambda hotel: hotel["price"])

