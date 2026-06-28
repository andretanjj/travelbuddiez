from app.services import nlp_service


def test_article_to_text_uses_title_and_original_description():
    article = {
        "title": "Japan issues flood warning",
        "originalDescription": "Heavy rain may affect transport.",
    }

    result = nlp_service.article_to_text(article)

    assert result == "Japan issues flood warning. Heavy rain may affect transport."


def test_contains_phrase_matches_whole_phrase():
    text = "Heavy rain warning issued in Japan."

    assert nlp_service.contains_phrase(text, "rain") is True
    assert nlp_service.contains_phrase(text, "Japan") is True


def test_contains_phrase_does_not_match_partial_word():
    text = "Rainfall is expected tomorrow."

    assert nlp_service.contains_phrase(text, "rain") is False


def test_get_candidates_removes_duplicate_urls():
    articles = [
        {
            "title": "Japan flood warning",
            "originalDescription": "Flood warning in Tokyo.",
            "url": "https://example.com/a",
        },
        {
            "title": "Japan flood warning duplicate",
            "originalDescription": "Flood warning in Tokyo.",
            "url": "https://example.com/a",
        },
    ]

    result = nlp_service.get_candidates(articles, "JPN")

    assert len(result) == 1


def test_get_candidates_requires_destination_alias_for_known_country():
    articles = [
        {
            "title": "Flood warning issued",
            "originalDescription": "Heavy rain affects transport.",
            "url": "https://example.com/a",
        }
    ]

    result = nlp_service.get_candidates(articles, "JPN")

    assert result == []


def test_get_candidates_keeps_article_with_japan_alias():
    articles = [
        {
            "title": "Japan flood warning issued",
            "originalDescription": "Heavy rain may affect tourists.",
            "url": "https://example.com/a",
        }
    ]

    result = nlp_service.get_candidates(articles, "JPN")

    assert len(result) == 1
    assert result[0]["title"] == "Japan flood warning issued"


def test_cosine_similarity_same_direction():
    vector_a = [1, 0]
    vector_b = [1, 0]

    result = nlp_service.cosine_similarity(vector_a, vector_b)

    assert result == 1


def test_cosine_similarity_opposite_direction():
    vector_a = [1, 0]
    vector_b = [-1, 0]

    result = nlp_service.cosine_similarity(vector_a, vector_b)

    assert result == -1


def test_cosine_similarity_zero_vector_returns_zero():
    vector_a = [0, 0]
    vector_b = [1, 2]

    result = nlp_service.cosine_similarity(vector_a, vector_b)

    assert result == 0