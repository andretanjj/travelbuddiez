import os
from fastapi import APIRouter, Depends, HTTPException

from app.schemas.assistant_schema import (
    AssistantRequest,
    AssistantResponse,
)
from app.services.ai_chatbot_service.assistant_intent_service import classify_assistant_intent
from app.services.ai_chatbot_service.assistant_service import generate_assistant_reply
from app.services.ai_chatbot_service.destination_context_service import (
    detect_destination_codes,
    get_destination_context,
    get_recommendation_candidates,
)
# from app.data.mock.mock_travel_prices import add_mock_prices
from app.services.ai_chatbot_service.assistant_price_service import (
    resolve_flight_price_data,
    resolve_hotel_price_data,
)
from app.services.saved_travel_service import (
    get_saved_flights_for_user,
    get_saved_hotels_for_user,
    refresh_saved_flight_price,
    refresh_saved_hotel_price,
)
from app.services.travel_place_service import (
    find_travel_place_in_message,
    resolve_destination_airport,
)
from app.services.ai_chatbot_service.travel_preference_service import (
    get_missing_live_price_fields,
)

from app.services.auth_service import get_current_active_user

PRICE_INTENTS = {
    "flight_price_question",
    "hotel_price_question",
    "flight_and_hotel_price_question",
}

router = APIRouter(
    prefix="/assistant",
    tags=["assistant"],
)

USE_MOCK_TRAVEL_PRICES = (
    os.getenv("USE_MOCK_TRAVEL_PRICES", "false").lower()
    == "true"
)

@router.post(
    "/chat",
    response_model=AssistantResponse,
)
def chat_with_assistant(
    request: AssistantRequest,
    current_user=Depends(get_current_active_user)
) -> AssistantResponse:
    try:
        print(
            "Assistant request from:", 
            current_user.username,
        )
        # Use the current dashboard destination when the question does not
        # explicitly name a country.
        print("Before destination detection")
        destination_codes = detect_destination_codes(request.message)
        print("After destination detection")

        if (
            not destination_codes
            and request.current_destination_code
        ):
            destination_codes = [
                request.current_destination_code.upper()
            ]

        intent = classify_assistant_intent(
            message=request.message,
            has_destination=bool(destination_codes),
            has_preferences=request.travel_preferences is not None,
        )

        if intent == "prompt_injection":
            return AssistantResponse(
                reply=(
                    "I can help with travel recommendations and trip "
                    "planning, but I cannot provide or override internal "
                    "instructions."
                ),
                intent=intent,
                destinations_used=[],
                missing_fields=[],
                data_last_updated=None,
            )

        if intent == "irrelevant":
            return AssistantResponse(
                reply=(
                    "I’m designed to help with travel recommendations "
                    "and trip planning. You can ask me about destinations, "
                    "itineraries, packing, transport, safety or budgeting."
                ),
                intent=intent,
                destinations_used=[],
                missing_fields=[],
                data_last_updated=None,
            )

        destination_data: list[dict] = []
        saved_item_data = None
        flight_price_data = None
        hotel_price_data = None

        # Retrieve destination context before resolving airport codes.
        if intent == "destination_recommendation":
            destination_data = get_recommendation_candidates(
                limit=10
            )
        elif destination_codes:
            destination_data = get_destination_context(
                destination_codes
            )

        # Handle questions about the user's saved flights.
        if intent == "saved_flight_question":
            if request.saved_flight_id is not None:
                saved_item_data = refresh_saved_flight_price(
                    username=current_user.username,
                    saved_flight_id=request.saved_flight_id,
                )
            else:
                saved_item_data = get_saved_flights_for_user(
                    username=current_user.username,
                )

        # Handle questions about the user's saved hotels.
        elif intent == "saved_hotel_question":
            if request.saved_hotel_id is not None:
                saved_item_data = refresh_saved_hotel_price(
                    username=current_user.username,
                    saved_hotel_id=request.saved_hotel_id,
                )
            else:
                saved_item_data = get_saved_hotels_for_user(
                    username=current_user.username,
                )

        # Handle new live flight/hotel searches.
        if intent in PRICE_INTENTS:
            preferences = request.travel_preferences

            missing_fields = get_missing_price_fields(
                intent=intent,
                preferences=preferences,
                has_destination=bool(destination_data),
            )

            if missing_fields:
                return AssistantResponse(
                    reply=build_missing_information_reply(
                        missing_fields
                    ),
                    intent="missing_information",
                    destinations_used=destination_codes,
                    missing_fields=missing_fields,
                    data_last_updated=None,
                )

            selected_destination = destination_data[0]

            # First try to detect a city or airport directly from the user's question.
            #
            # Example:
            # "Find me the cheapest trip to Tokyo"
            # -> detects Tokyo / TYO
            question_text = extract_question_text(
                request.message
            )

            print(
                "[ASSISTANT] Question used for place detection:",
                question_text,
            )

            requested_place = find_travel_place_in_message(
                message=question_text,
                mode="flight",
            )

            print(
                "[ASSISTANT] Place detected from message:",
                requested_place,
            )

            if (
                requested_place is not None
                and requested_place.get("code")
            ):
                destination_place = requested_place

            else:
                # No specific city/airport was mentioned in the question.
                # Fall back to the default city stored in destinations.
                destination_city = (
                    selected_destination.get("city")
                    or selected_destination.get("country_name")
                )

                print(
                    "[ASSISTANT] No place detected from message. "
                    "Falling back to:",
                    destination_city,
                )

                destination_place = resolve_destination_airport(
                    destination=destination_city,
                )


            if destination_place is None:
                return AssistantResponse(
                    reply=(
                        "I found the destination, but I could not "
                        "find a suitable airport or city for the "
                        "live price search."
                    ),
                    intent=intent,
                    destinations_used=destination_codes,
                    missing_fields=[],
                    data_last_updated=None,
                )


            destination_airport_code = destination_place["code"].upper()
            origin_airport_code = preferences.origin.upper()


            # Safety check:
            # prevent accidental searches such as SIN -> SIN
            if destination_airport_code == origin_airport_code:
                return AssistantResponse(
                    reply=(
                        "I could not determine the destination airport correctly. "
                        "Please specify the city you want to travel to."
                    ),
                    intent=intent,
                    destinations_used=destination_codes,
                    missing_fields=[],
                    data_last_updated=None,
                )

            print(
                "[ASSISTANT] Resolved live search destination:",
                destination_place.get("name"),
                "->",
                destination_airport_code,
            )

            if intent in {
                "flight_price_question",
                "flight_and_hotel_price_question",
            }:
                flight_price_data = resolve_flight_price_data(
                    username=current_user.username,
                    origin=origin_airport_code,
                    destination=destination_airport_code,
                    departure_date=str(
                        preferences.departure_date
                    ),
                    return_date=(
                        str(preferences.return_date)
                        if preferences.return_date
                        else None
                    ),
                    adults=preferences.travellers,
                )

            if intent in {
                "hotel_price_question",
                "flight_and_hotel_price_question",
            }:
                hotel_price_data = resolve_hotel_price_data(
                    username=current_user.username,
                    destination=destination_airport_code,
                    check_in_date=str(
                        preferences.departure_date
                    ),
                    check_out_date=str(
                        preferences.return_date
                    ),
                    adults=preferences.travellers,
                )

        reply = generate_assistant_reply(
            user_message=request.message,
            destination_data=destination_data,
            conversation_history=(
                request.conversation_history
            ),
            travel_preferences=request.travel_preferences,
            intent=intent,
            saved_item_data=saved_item_data,
            flight_price_data=flight_price_data,
            hotel_price_data=hotel_price_data,
        )

        used_codes = [
            destination["country_code"]
            for destination in destination_data
        ]

        update_times = [
            destination["last_updated"]
            for destination in destination_data
            if destination.get("last_updated")
        ]

        latest_update = (
            max(update_times)
            if update_times
            else None
        )

        return AssistantResponse(
            reply=reply,
            intent=intent,
            destinations_used=used_codes,
            missing_fields=[],
            data_last_updated=latest_update,
        )

    except HTTPException:
        raise

    except Exception as error:
        print(
            "Travel assistant error:",
            type(error).__name__,
            error,
        )

        error_text = str(error).casefold()

        if (
            "429" in error_text
            or "resource_exhausted" in error_text
            or "rate limit" in error_text
        ):
            raise HTTPException(
                status_code=429,
                detail=(
                    "The AI assistant has reached its temporary "
                    "usage limit. Please try again shortly."
                ),
            )

        raise HTTPException(
            status_code=503,
            detail=(
                "The TravelBuddiez assistant is temporarily "
                "unavailable."
            ),
        )

def get_missing_price_fields(
    intent: str,
    preferences,
    has_destination: bool,
) -> list[str]:
    """
    Returns only the fields needed for the selected price-search intent.

    A combined flight-and-hotel search requires:
    - origin
    - departure date
    - return date
    - travellers
    - destination
    """

    missing_fields: list[str] = []

    if not has_destination:
        missing_fields.append("destination")

    if preferences is None:
        if intent in {
            "flight_price_question",
            "flight_and_hotel_price_question",
        }:
            missing_fields.extend([
                "origin",
                "departure_date",
                "travellers",
            ])

        if intent in {
            "hotel_price_question",
            "flight_and_hotel_price_question",
        }:
            missing_fields.extend([
                "departure_date",
                "return_date",
                "travellers",
            ])

        return list(dict.fromkeys(missing_fields))

    if intent in {
        "flight_price_question",
        "flight_and_hotel_price_question",
    }:
        if not preferences.origin:
            missing_fields.append("origin")

        if not preferences.departure_date:
            missing_fields.append("departure_date")

        if not preferences.travellers:
            missing_fields.append("travellers")

    if intent in {
        "hotel_price_question",
        "flight_and_hotel_price_question",
    }:
        if not preferences.departure_date:
            missing_fields.append("departure_date")

        if not preferences.return_date:
            missing_fields.append("return_date")

        if not preferences.travellers:
            missing_fields.append("travellers")

    # A combined plan needs a return date for the round trip.
    if (
        intent == "flight_and_hotel_price_question"
        and not preferences.return_date
    ):
        missing_fields.append("return_date")

    return list(dict.fromkeys(missing_fields))

def build_missing_information_reply(
    missing_fields: list[str],
) -> str:
    labels = {
        "origin": "departure airport",
        "destination": "destination",
        "departure_date": "departure date",
        "return_date": "return date",
        "travellers": "number of travellers",
    }

    readable_fields = [
        labels.get(field, field)
        for field in missing_fields
    ]

    if len(readable_fields) == 1:
        joined_fields = readable_fields[0]
    else:
        joined_fields = (
            ", ".join(readable_fields[:-1])
            + f" and {readable_fields[-1]}"
        )

    return (
        "To search current flight or hotel prices, "
        f"please provide your {joined_fields}."
    )

def extract_question_text(message: str) -> str:
    """
    Extracts only the user's actual question from a frontend-formatted
    assistant message.

    Example:
        Destination: japan
        Departure airport: SIN
        ...
        Question: cheapest trip to Tokyo

    Returns:
        cheapest trip to Tokyo
    """

    marker = "Question:"

    if marker.casefold() in message.casefold():
        index = message.casefold().find(marker.casefold())

        return message[index + len(marker):].strip()

    return message.strip()