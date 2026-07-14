import os
import requests


DUFFEL_API_TOKEN = os.getenv("DUFFEL_API_TOKEN")
DUFFEL_BASE_URL = os.getenv("DUFFEL_BASE_URL", "https://api.duffel.com")
DUFFEL_API_VERSION = os.getenv("DUFFEL_API_VERSION", "v2")


def build_passengers(adults: int):
    """
    Builds the passenger list for Duffel.

    Duffel needs passenger data in the offer request.
    For now, we only support adult passengers because the frontend only has an adults field.
    """

    passengers = []

    for _ in range(adults):
        passengers.append(
            {
                "type": "adult",
            }
        )

    return passengers


def normalise_duffel_offer(offer):
    """
    Converts one Duffel offer into the simplified FlightResult shape used by frontend.

    Duffel offers can include connecting flights.
    Example:
    - Segment 1: SIN -> SGN
    - Segment 2: SGN -> HND

    For display, we should show the full slice route:
    - SIN -> HND
    """

    first_slice = offer["slices"][0]

    # A direct flight has 1 segment.
    # A connecting flight has 2 or more segments.
    segments = first_slice["segments"]

    # First segment contains the real starting airport.
    first_segment = segments[0]

    # Last segment contains the final destination airport.
    last_segment = segments[-1]

    # Duffel returns total_amount as a string, so convert it to float.
    total_amount = float(offer["total_amount"])

    # Duffel owner is usually the airline selling the offer.
    airline_name = offer["owner"]["name"]

    number_of_segments = len(segments)

    if number_of_segments == 1:
        stops = "Direct"
    else:
        stops = f"{number_of_segments - 1} stop(s)"

    return {
        "id": offer["id"],

        # Use the final destination city/country, not the first layover city.
        "city": last_segment["destination"]["city_name"] or last_segment["destination"]["name"],
        "country": last_segment["destination"]["iata_country_code"],

        # Show full requested journey, not the first segment only.
        "route": f"{first_segment['origin']['iata_code']} → {last_segment['destination']['iata_code']}",

        "price": total_amount,
        "currency": offer["total_currency"],
        "airline": airline_name,
        "duration": first_slice["duration"],
        "stops": stops,
        "departureDate": first_segment["departing_at"][:10],
    }


def search_duffel_flights(origin: str, destination: str, departure_date: str, adults: int):
    """
    Calls Duffel's create offer request endpoint.

    Current limitation:
    - One-way flights only.
    - Adult passengers only.
    - Origin/destination should be IATA airport or city codes, e.g. SIN, NRT, TYO.
    """

    if not DUFFEL_API_TOKEN:
        raise RuntimeError("DUFFEL_API_TOKEN is missing")

    url = f"{DUFFEL_BASE_URL}/air/offer_requests"

    headers = {
        "Authorization": f"Bearer {DUFFEL_API_TOKEN}",
        "Content-Type": "application/json",
        "Duffel-Version": DUFFEL_API_VERSION,
    }

    payload = {
        "data": {
            "slices": [
                {
                    "origin": origin.upper(),
                    "destination": destination.upper(),
                    "departure_date": departure_date,
                }
            ],
            "passengers": build_passengers(adults),
            "cabin_class": "economy",
        }
    }

    response = requests.post(url, headers=headers, json=payload, timeout=20)

    if not response.ok:
        # Raise a useful error so the caller can fallback to mock data.
        raise RuntimeError(f"Duffel request failed: {response.status_code} {response.text}")

    response_data = response.json()

    offers = response_data["data"].get("offers", [])

    normalised_offers = []

    for offer in offers[:10]:
        normalised_offers.append(normalise_duffel_offer(offer))

    return sorted(normalised_offers, key=lambda flight: flight["price"])