import os
from fastapi import APIRouter, HTTPException

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
from app.data.mock.mock_travel_prices import add_mock_prices

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
) -> AssistantResponse:
    try:
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

        if intent == "destination_recommendation":
            destination_data = get_recommendation_candidates(
                limit=10
            )

        elif destination_codes:
            destination_data = get_destination_context(
                destination_codes
            )

        else:
            # General advice such as:
            # "How should I divide my travel budget?"
            destination_data = []

        destination_data = add_mock_prices(destination_data)

        reply = generate_assistant_reply(
            user_message=request.message,
            destination_data=destination_data,
            conversation_history=request.conversation_history,
            travel_preferences=request.travel_preferences,
            intent=intent,
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

        latest_update = max(update_times) if update_times else None

        return AssistantResponse(
            reply=reply,
            intent=intent,
            destinations_used=used_codes,
            missing_fields=[],
            data_last_updated=latest_update,
        )

    except Exception as error:
        print(f"Travel assistant error: {error}")

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