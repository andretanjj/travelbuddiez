from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

class TravelPreferences(BaseModel):
    origin: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
        description="Departure airport IATA code, such as SIN",
    )
    departure_date: date | None = None
    return_date: date | None = None
    travellers: int | None = Field(default=None, ge=1, le=20)
    budget: Literal["low", "medium", "high"] | None = None
    destination_type: list[
        Literal["city", "beach", "nature", "culture", "mixed"]
    ] = Field(
        default_factory=list,
        max_length=5,
    )
    safety_priority: Literal["low", "medium", "high"] | None = None
    interests: list[str] = Field(
        default_factory=list,
        max_length=10,
    )

    travel_pace: Literal[
        "relaxed",
        "balanced",
        "packed",
    ] | None = None

    accommodation_preference: Literal[
        "hostel",
        "budget_hotel",
        "hotel",
        "resort",
        "no_preference",
    ] | None = None

    transport_preference: Literal[
        "public_transport",
        "walking",
        "private_transport",
        "no_preference",
    ] | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.departure_date is not None
            and self.return_date is not None
            and self.return_date <= self.departure_date
        ) :
            raise ValueError(
                "Return date must be after departure date."
            )
        return self

    @property
    def trip_duration_days(self) -> int | None:
        if not self.departure_date or not self.return_date:
            return None

        return (self.return_date - self.departure_date).days

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)

AssistantIntent = Literal[
    "destination_recommendation",
    "travel_advice",
    "destination_question",
    "missing_information",
    "irrelevant",
    "prompt_injection",
]

class AssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)

    conversation_history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=10,
    )

    # Structured values submitted through the travel search form.
    travel_preferences: TravelPreferences | None = None

    # Optional destination code supplied by the dashboard.
    current_destination_code: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
        description="Destination ISO alpha-3 code, such as JPN",
    )

class AssistantResponse(BaseModel):
    reply: str

    intent: AssistantIntent

    destinations_used: list[str] = Field(
        default_factory=list,
    )

    missing_fields: list[str] = Field(
        default_factory=list,
    )

    data_last_updated: str | None = None