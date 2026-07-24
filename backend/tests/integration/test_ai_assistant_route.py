from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import (
    get_current_active_user,
)


class FakeUser:
    username = "testuser"


def override_current_user():
    return FakeUser()


app.dependency_overrides[
    get_current_active_user
] = override_current_user

client = TestClient(app)

def test_assistant_rejects_missing_message():
    response = client.post(
        "/assistant/chat",
        json={
            "travel_preferences": {
                "origin": "SIN",
                "departure_date": "2026-08-10",
                "travellers": 1,
            }
        },
    )

    assert response.status_code == 422

def test_assistant_flight_price_request(
    mocker,
):
    mocker.patch(
        "app.routes.ai_assistant."
        "detect_destination_codes",
        return_value=["TYO"],
    )

    mocker.patch(
        "app.routes.ai_assistant."
        "classify_assistant_intent",
        return_value="flight_price_question",
    )

    mocker.patch(
        "app.routes.ai_assistant."
        "resolve_flight_price_data",
        return_value={
            "source": "new_search",
            "is_saved": False,
            "results": [
                {
                    "price": 420,
                    "currency": "SGD",
                    "route": "SIN → TYO",
                }
            ],
        },
    )

    mocker.patch(
        "app.routes.ai_assistant."
        "get_destination_context",
        return_value=[],
    )

    mocker.patch(
        "app.routes.ai_assistant."
        "generate_assistant_reply",
        return_value=(
            "The cheapest flight found is S$420."
        ),
    )

    response = client.post(
        "/assistant/chat",
        json={
            "message": (
                "Find the cheapest flight to Tokyo"
            ),
            "travel_preferences": {
                "origin": "SIN",
                "departure_date": "2026-08-10",
                "travellers": 1,
            },
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["intent"] == "flight_price_question"
    assert "S$420" in body["reply"]

def test_assistant_requests_missing_flight_fields(
    mocker,
):
    mocker.patch(
        "app.routes.ai_assistant."
        "detect_destination_codes",
        return_value=["TYO"],
    )

    mocker.patch(
        "app.routes.ai_assistant."
        "classify_assistant_intent",
        return_value="flight_price_question",
    )

    response = client.post(
        "/assistant/chat",
        json={
            "message": (
                "Find the cheapest flight to Tokyo"
            ),
            "travel_preferences": {
                "travellers": 1,
            },
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["intent"] == "missing_information"
    assert "origin" in body["missing_fields"]
    assert "departure_date" in body["missing_fields"]

def test_assistant_returns_429_for_gemini_rate_limit(
    mocker,
):
    mocker.patch(
        "app.routes.ai_assistant."
        "detect_destination_codes",
        return_value=["JPN"],
    )

    mocker.patch(
        "app.routes.ai_assistant."
        "classify_assistant_intent",
        return_value="destination_question",
    )

    mocker.patch(
        "app.routes.ai_assistant."
        "get_destination_context",
        return_value=[],
    )

    mocker.patch(
        "app.routes.ai_assistant."
        "generate_assistant_reply",
        side_effect=RuntimeError(
            "429 RESOURCE_EXHAUSTED"
        ),
    )

    response = client.post(
        "/assistant/chat",
        json={
            "message": "Is Japan safe?",
        },
    )

    assert response.status_code == 429
    assert "usage limit" in response.json()["detail"]