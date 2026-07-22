from fastapi.testclient import TestClient


VALID_REQUEST = {
    "message": "Is Japan safe to visit?",
    "conversation_history": [],
    "current_destination_code": None,
    "travel_preferences": None,
}


def test_missing_message_returns_422(
    client: TestClient,
) -> None:
    response = client.post(
        "/assistant/chat",
        json={},
    )

    assert response.status_code == 422


def test_valid_request_returns_reply(
    client: TestClient,
    monkeypatch,
) -> None:
    def fake_detect_destination_codes(
        message: str,
    ) -> list[str]:
        return ["JPN"]

    def fake_classify_assistant_intent(**kwargs) -> str:
        return "destination_info"

    def fake_get_destination_context(
        destination_codes: list[str],
    ) -> list[dict]:
        return [
            {
                "country_code": "JPN",
                "country_name": "Japan",
                "last_updated": None,
            }
        ]

    def fake_generate_assistant_reply(**kwargs) -> str:
        return "Japan is generally suitable for travel."

    monkeypatch.setattr(
        "app.routes.ai_assistant.detect_destination_codes",
        fake_detect_destination_codes,
    )

    monkeypatch.setattr(
        "app.routes.ai_assistant.classify_assistant_intent",
        fake_classify_assistant_intent,
    )

    monkeypatch.setattr(
        "app.routes.ai_assistant.get_destination_context",
        fake_get_destination_context,
    )

    monkeypatch.setattr(
        "app.routes.ai_assistant.add_mock_prices",
        lambda destination_data: destination_data,
    )

    monkeypatch.setattr(
        "app.routes.ai_assistant.generate_assistant_reply",
        fake_generate_assistant_reply,
    )

    response = client.post(
        "/assistant/chat",
        json=VALID_REQUEST,
    )

    print("Status:", response.status_code)
    print("Body:", response.json())

    assert response.status_code == 200
    assert response.json()["reply"] == (
        "Japan is generally suitable for travel."
    )
    assert response.json()["destinations_used"] == ["JPN"]

def test_model_failure_returns_503(
    client: TestClient,
    monkeypatch,
) -> None:
    def fake_detect_destination_codes(message: str) -> list[str]:
        return ["JPN"]

    def fake_classify_assistant_intent(
        message: str,
        has_destination: bool,
        has_preferences: bool,
    ) -> str:
        return "destination_info"

    def fake_get_destination_context(
        destination_codes: list[str],
    ) -> list[dict]:
        return [
            {
                "country_code": "JPN",
                "country_name": "Japan",
                "last_updated": None,
            }
        ]

    def fake_generate_assistant_reply(
        *,
        user_message,
        destination_data,
        conversation_history,
        travel_preferences,
        intent,
    ) -> str:
        raise RuntimeError("503 UNAVAILABLE")

    monkeypatch.setattr(
        "app.routes.ai_assistant.detect_destination_codes",
        fake_detect_destination_codes,
    )

    monkeypatch.setattr(
        "app.routes.ai_assistant.classify_assistant_intent",
        fake_classify_assistant_intent,
    )

    monkeypatch.setattr(
        "app.routes.ai_assistant.get_destination_context",
        fake_get_destination_context,
    )

    monkeypatch.setattr(
        "app.routes.ai_assistant.add_mock_prices",
        lambda destination_data: destination_data,
    )

    monkeypatch.setattr(
        "app.routes.ai_assistant.generate_assistant_reply",
        fake_generate_assistant_reply,
    )

    response = client.post(
        "/assistant/chat",
        json=VALID_REQUEST,
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": (
            "The TravelBuddiez assistant is temporarily "
            "unavailable."
        )
    }

def test_rate_limit_returns_429(
    client: TestClient,
    monkeypatch,
) -> None:
    def fake_generate_assistant_reply(**kwargs) -> str:
        raise RuntimeError("429 RESOURCE_EXHAUSTED")

    monkeypatch.setattr(
        "app.routes.ai_assistant.detect_destination_codes",
        lambda message: [],
    )

    monkeypatch.setattr(
        "app.routes.ai_assistant.classify_assistant_intent",
        lambda **kwargs: "general_advice",
    )

    monkeypatch.setattr(
        "app.routes.ai_assistant.add_mock_prices",
        lambda destination_data: destination_data,
    )

    monkeypatch.setattr(
        "app.routes.ai_assistant.generate_assistant_reply",
        fake_generate_assistant_reply,
    )

    response = client.post(
        "/assistant/chat",
        json=VALID_REQUEST,
    )

    assert response.status_code == 429
    assert response.json() == {
        "detail": (
            "The AI assistant has reached its temporary "
            "usage limit. Please try again shortly."
        )
    }