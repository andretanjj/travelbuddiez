import logging
import os
import requests

logger = logging.getLogger("uvicorn.error")


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

    logger.info(
        "[DUFFEL] Calling live Duffel API: %s → %s, date=%s, adults=%s",
        origin.upper(),
        destination.upper(),
        departure_date,
        adults,
    )

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

    logger.info(
        "[DUFFEL] HTTP response received with status %s",
        response.status_code,
    )

    if not response.ok:
        logger.error(
            "[DUFFEL] Live API request failed with status %s",
            response.status_code,
        )

        raise RuntimeError(
            f"Duffel request failed: "
            f"{response.status_code} {response.text}"
        )

    response_data = response.json()

    offers = response_data["data"].get("offers", [])

    logger.info(
        "[DUFFEL] Live API returned %s raw offer(s)",
        len(offers),
    )

    normalised_offers = []

    for offer in offers[:20]:
        try:
            owner = offer.get("owner", {})
            owner_name = owner.get("name", "")
            owner_iata_code = owner.get("iata_code", "")

            # Duffel Airways is a sandbox airline used for test-mode integration.
            # Exclude it from TravelBuddiez user-facing search results.
            if owner_name == "Duffel Airways" or owner_iata_code == "ZZ":
                logger.info(
                    "[DUFFEL] Skipping sandbox offer from Duffel Airways: %s",
                    offer.get("id"),
                )
                continue

            normalised_offer = normalise_duffel_offer(offer)

            if normalised_offer["price"] > 0:
                normalised_offers.append(normalised_offer)

        except Exception as error:
            logger.exception(
                "[DUFFEL] Failed to normalise offer %s: %s",
                offer.get("id"),
                error,
            )

    sorted_offers = sorted(normalised_offers,key=lambda flight: flight["price"])

    logger.info(
        "[DUFFEL] Successfully normalised %s live flight offer(s)",
        len(sorted_offers),
    )

    return sorted_offers