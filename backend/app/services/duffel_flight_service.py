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


def normalise_slice(slice_data):
    """
    Converts one Duffel slice into the simplified journey details
    used by TravelBuddiez.

    A slice may contain one segment for a direct flight or multiple
    segments when connections are required.
    """

    segments = slice_data["segments"]

    first_segment = segments[0]
    last_segment = segments[-1]

    number_of_segments = len(segments)

    if number_of_segments == 1:
        stops = "Direct"
    else:
        stops = f"{number_of_segments - 1} stop(s)"

    return {
        "route": (
            f"{first_segment['origin']['iata_code']} → "
            f"{last_segment['destination']['iata_code']}"
        ),
        "departureDate": first_segment["departing_at"][:10],
        "departureAt": first_segment.get("departing_at"),
        "duration": slice_data["duration"],
        "stops": stops,
        "firstSegment": first_segment,
        "lastSegment": last_segment,
    }


def normalise_duffel_offer(offer):
    """
    Converts a Duffel offer into the simplified FlightResult shape
    used by the TravelBuddiez frontend.

    offer["slices"][0] = outbound journey
    offer["slices"][1] = return journey, when present
    """

    slices = offer["slices"]

    # Every valid offer has an outbound slice.
    outbound = normalise_slice(slices[0])

    # A second slice means this is a round-trip offer.
    inbound = (
        normalise_slice(slices[1])
        if len(slices) > 1
        else None
    )

    total_amount = float(offer["total_amount"])
    airline_name = offer["owner"]["name"]

    outbound_first_segment = outbound["firstSegment"]
    outbound_last_segment = outbound["lastSegment"]
    # The first segment of the inbound slice identifies the first
    # return flight. It is None for one-way journeys.
    inbound_first_segment = (inbound["firstSegment"] if inbound else None)

    return {
        "id": offer["id"],
        "providerItemId": offer["id"],

        "city": (
            outbound_last_segment["destination"].get("city_name")
            or outbound_last_segment["destination"]["name"]
        ),
        "country": outbound_last_segment[
            "destination"
        ]["iata_country_code"],

        # Outbound journey.
        "route": outbound["route"],
        "departureDate": outbound["departureDate"],
        "departureAt": outbound["departureAt"],
        "duration": outbound["duration"],
        "stops": outbound["stops"],

        # Return journey.
        "returnRoute": (
            inbound["route"]
            if inbound
            else None
        ),
        "returnDate": (
            inbound["departureDate"]
            if inbound
            else None
        ),
        "returnDepartureAt": (
            inbound["departureAt"]
            if inbound
            else None
        ),
        "returnDuration": (
            inbound["duration"]
            if inbound
            else None
        ),
        "returnStops": (
            inbound["stops"]
            if inbound
            else None
        ),

        "returnFlightNumber": (
            inbound_first_segment.get(
                "marketing_carrier_flight_number"
            )
            if inbound_first_segment
            else None
        ),

        # Duffel total_amount represents the full offer.
        "price": total_amount,
        "currency": offer["total_currency"],

        "airline": airline_name,
        "flightNumber": outbound_first_segment.get(
            "marketing_carrier_flight_number"
        ),
    }


def search_duffel_flights(origin: str, destination: str, departure_date: str, adults: int, return_date: str | None = None):
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

    # Duffel represents each direction of travel as a slice.
    # One-way journey = one slice.
    # Round trip = outbound slice + inbound slice.
    slices = [
        {
            "origin": origin.upper(),
            "destination": destination.upper(),
            "departure_date": departure_date,
        }
    ]

    if return_date:
        slices.append(
            {
                # Reverse the route for the inbound journey.
                "origin": destination.upper(),
                "destination": origin.upper(),
                "departure_date": return_date,
            }
        )

    payload = {
        "data": {
            "slices": slices,
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

    for offer in offers:
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
