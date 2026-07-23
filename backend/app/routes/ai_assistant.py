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

from app.services.auth_service import get_current_active_user

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

        flight_price_data = None
        hotel_price_data = None
        saved_item_data = None
        missing_fields: list[str] = []

        preferences = request.travel_preferences

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
        missing_fields: list[str] = []

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

        if intent in {
            "flight_price_question",
            "flight_and_hotel_price_question",
        }:
            flight_missing: list[str] = []

            if preferences is None:
                flight_missing.extend([
                    "origin",
                    "departure_date",
                    "travellers",
                ])
            else:
                if not preferences.origin:
                    flight_missing.append("origin")

                if not preferences.departure_date:
                    flight_missing.append(
                        "departure_date"
                    )

                if not preferences.travellers:
                    flight_missing.append(
                        "travellers"
                    )

            if not destination_codes:
                flight_missing.append("destination")

            missing_fields.extend(flight_missing)

            if not flight_missing:
                flight_price_data = resolve_flight_price_data(
                    username=current_user.username,
                    origin=preferences.origin,
                    destination=destination_codes[0],
                    departure_date=str(
                        preferences.departure_date
                    ),
                    adults=preferences.travellers,
                )

        # New or general hotel-price search
        if intent in {
            "hotel_price_question",
            "flight_and_hotel_price_question",
        }:
            hotel_missing: list[str] = []

            if preferences is None:
                hotel_missing.extend([
                    "check_in_date",
                    "check_out_date",
                    "travellers",
                ])
            else:
                if not preferences.check_in_date:
                    hotel_missing.append(
                        "check_in_date"
                    )

                if not preferences.check_out_date:
                    hotel_missing.append(
                        "check_out_date"
                    )

                if not preferences.travellers:
                    hotel_missing.append(
                        "travellers"
                    )

            if not destination_codes:
                hotel_missing.append("destination")

            missing_fields.extend(hotel_missing)

            if not hotel_missing:
                hotel_price_data = resolve_hotel_price_data(
                    username=current_user.username,
                    destination=destination_codes[0],
                    check_in_date=str(
                        preferences.check_in_date
                    ),
                    check_out_date=str(
                        preferences.check_out_date
                    ),
                    adults=preferences.travellers,
                )

        missing_fields = list(
            dict.fromkeys(missing_fields)
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

        # Destination context
        if intent == "destination_recommendation":
            destination_data = (
                get_recommendation_candidates(
                    limit=10
                )
            )

        elif destination_codes:
            destination_data = get_destination_context(
                destination_codes
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


def build_missing_information_reply(
    missing_fields: list[str],
) -> str:
    labels = {
        "origin": "departure airport",
        "destination": "destination",
        "departure_date": "departure date",
        "travellers": "number of travellers",
        "check_in_date": "hotel check-in date",
        "check_out_date": "hotel check-out date",
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