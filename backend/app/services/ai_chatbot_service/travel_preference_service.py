from app.schemas.assistant_schema import TravelPreferences

LIVE_PRICE_FIELDS = [
    "origin",
    "departure_date",
    "return_date",
    "travellers",
]


def get_missing_live_price_fields(
    preferences: TravelPreferences | None,
) -> list[str]:
    if preferences is None:
        return LIVE_PRICE_FIELDS.copy()

    missing: list[str] = []

    for field_name in LIVE_PRICE_FIELDS:
        value = getattr(preferences, field_name)

        if value is None or value == "":
            missing.append(field_name)

    return missing


def format_travel_preferences(
    preferences: TravelPreferences | None,
) -> dict:
    if preferences is None:
        return {}

    result = preferences.model_dump(mode="json")
    result["trip_duration_days"] = preferences.trip_duration_days

    return result