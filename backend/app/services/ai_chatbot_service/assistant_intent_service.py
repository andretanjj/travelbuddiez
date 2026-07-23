from typing import Literal
from app.schemas.assistant_schema import AssistantIntent

PROMPT_INJECTION_PHRASES = {
    "ignore previous instructions",
    "ignore your instructions",
    "reveal your system prompt",
    "show your system prompt",
    "override your rules",
    "act as a different assistant",
}

RECOMMENDATION_PHRASES = {
    "recommend",
    "where should i go",
    "where can i go",
    "suggest a destination",
    "best destination",
    "which country should",
    "which place should",
    "holiday ideas",
}

PLANNING_KEYWORDS = {
    "itinerary",
    "plan my trip",
    "travel plan",
    "what should i do",
    "things to do",
    "attractions",
    "activities",
    "pack",
    "packing",
    "transport",
    "getting around",
    "budget",
    "how much should i bring",
    "where should i stay",
    "hotel area",
    "neighbourhood",
    "food",
    "restaurant",
    "visa",
    "airport",
}

DESTINATION_QUESTION_KEYWORDS = {
    "safe",
    "safety",
    "weather",
    "advisory",
    "risk",
    "news",
    "travel score",
    "condition",
    "compare",
    "better",
}

FLIGHT_PRICE_PHRASES = {
    "flight",
    "flights",
    "airfare",
    "plane ticket",
    "flight price",
    "flight prices",
    "cheapest flight",
    "cost to fly",
}

HOTEL_PRICE_PHRASES = {
    "hotel",
    "hotels",
    "accommodation",
    "hotel price",
    "hotel prices",
    "room price",
    "cheapest hotel",
    "cost to stay",
}

SAVED_FLIGHT_PHRASES = {
    "saved flight",
    "my saved flight",
    "flight i saved",
    "saved airfare",
    "has my flight price changed",
    "did my flight price drop",
    "is my saved flight still the cheapest",
}

SAVED_HOTEL_PHRASES = {
    "saved hotel",
    "my saved hotel",
    "hotel i saved",
    "saved accommodation",
    "has my hotel price changed",
    "did my hotel price drop",
    "is my saved hotel still the cheapest",
}


def classify_assistant_intent(
    message: str,
    has_destination: bool,
    has_preferences: bool,
) -> AssistantIntent:
    text = message.casefold().strip()

    if any(
        phrase in text
        for phrase in PROMPT_INJECTION_PHRASES
    ):
        return "prompt_injection"

    if any(
        phrase in text
        for phrase in SAVED_FLIGHT_PHRASES
    ):
        return "saved_flight_question"

    if any(
        phrase in text
        for phrase in SAVED_HOTEL_PHRASES
    ):
        return "saved_hotel_question"

    mentions_flight = any(
        phrase in text
        for phrase in FLIGHT_PRICE_PHRASES
    )

    mentions_hotel = any(
        phrase in text
        for phrase in HOTEL_PRICE_PHRASES
    )

    if mentions_flight and mentions_hotel:
        return "flight_and_hotel_price_question"

    if mentions_flight:
        return "flight_price_question"

    if mentions_hotel:
        return "hotel_price_question"

    if any(
        phrase in text
        for phrase in RECOMMENDATION_PHRASES
    ):
        return "destination_recommendation"

    if any(
        keyword in text
        for keyword in PLANNING_KEYWORDS
    ):
        return "travel_advice"

    if has_destination:
        return "destination_question"

    if has_preferences:
        return "destination_recommendation"

    return "irrelevant"