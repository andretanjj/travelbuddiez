# tests/test_destination_detection.py

from app.services.ai_chatbot_service.destination_context_service import (
    detect_destination_codes,
    contains_complete_phrase,
)


def test_detects_japan() -> None:
    result = detect_destination_codes(
        "Is Japan safe to visit in December?"
    )

    assert "JPN" in result


def test_detects_multiple_destinations() -> None:
    result = detect_destination_codes(
        "Should I travel to Japan or Thailand?"
    )

    assert "JPN" in result
    assert "THA" in result


def test_does_not_detect_partial_country_name() -> None:
    result = detect_destination_codes(
        "I want to compare destinations."
    )

    assert "ARE" not in result


def test_returns_empty_list_when_no_destination_found() -> None:
    result = detect_destination_codes(
        "Recommend somewhere with good food."
    )

    assert result == []

def test_complete_phrase_matches() -> None:
    assert contains_complete_phrase(
        "I want to visit South Korea.",
        "South Korea",
    )


def test_partial_word_does_not_match() -> None:
    assert not contains_complete_phrase(
        "I want to compare places.",
        "ARE",
    )


def test_matching_is_case_insensitive() -> None:
    assert contains_complete_phrase(
        "is JAPAN safe?",
        "Japan",
    )

def test_rejects_too_many_travellers(
    client: TestClient,
) -> None:
    response = client.post(
        "/assistant/chat",
        json={
            "message": "Plan a trip to Japan.",
            "conversation_history": [],
            "travel_preferences": {
                "travellers": 30,
            },
        },
    )

    assert response.status_code == 422

def test_accepts_valid_travel_preferences(
    client: TestClient,
    monkeypatch,
) -> None:
    def fake_generate_assistant_reply(request):
        return "Here is a suggested trip."

    monkeypatch.setattr(
        "app.routes.ai_assistant.generate_assistant_reply",
        fake_generate_assistant_reply,
    )

    response = client.post(
        "/assistant/chat",
        json={
            "message": "Plan a trip to Japan.",
            "conversation_history": [],
            "current_destination_code": "JPN",
            "travel_preferences": {
                "origin": "SIN",
                "travellers": 2,
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["reply"] == (
        "Here is a suggested trip."
    )