from app.data.travelscore import (
    calculate_travelscore,
    calculate_weather_deduction,
    calculate_news_deduction,
    calculate_advisory_deduction,
    get_risk_level,
    get_condition,
)


def test_weather_no_risk_string():
    weather = "clear sky, around 25°C"
    result = calculate_weather_deduction(weather)
    assert result["deduction"] == 0
    assert result["reasons"] == []


def test_weather_heavy_rain_deducts_20():
    weather = "heavy rain expected in the afternoon"
    result = calculate_weather_deduction(weather)
    assert result["deduction"] == 20
    assert "Weather risk" in result["reasons"]


def test_weather_extreme_hot_temperature_deducts_10():
    weather = {
        "condition": "clear sky",
        "temperature": 36,
    }

    result = calculate_weather_deduction(weather)
    assert result["deduction"] == 10
    assert "Extreme temperature" in result["reasons"]


def test_weather_storm_and_extreme_temperature_deducts_30():
    weather = {
        "condition": "thunderstorm",
        "temperature": 36,
    }

    result = calculate_weather_deduction(weather)
    assert result["deduction"] == 30
    assert "Weather risk" in result["reasons"]
    assert "Extreme temperature" in result["reasons"]


def test_news_no_risk():
    news = [
        {
            "title": "Japan tourism numbers rise",
            "originalDescription": "Tourists continue to visit major attractions.",
            "abstractedSummary": "General tourism update with no safety issue.",
        }
    ]

    result = calculate_news_deduction(news)
    assert result["deduction"] == 0
    assert result["reasons"] == []


def test_news_high_risk_deducts_25():
    news = [
        {
            "title": "Earthquake causes airport disruption in Japan",
            "originalDescription": "Travellers are advised to check flights.",
            "abstractedSummary": "An earthquake has disrupted travel.",
        }
    ]

    result = calculate_news_deduction(news)
    assert result["deduction"] == 25
    assert "High-risk news" in result["reasons"]


def test_news_medium_risk_deducts_10():
    news = [
        {
            "title": "Transport strike causes delays",
            "originalDescription": "Some train services are delayed.",
            "abstractedSummary": "Transport disruption may affect travellers.",
        }
    ]

    result = calculate_news_deduction(news)
    assert result["deduction"] == 10
    assert "News risk" in result["reasons"]


def test_news_recovery_keywords_no_deduction():
    news = [
        {
            "title": "Airport reopened after storm",
            "originalDescription": "Flights have resumed and normal operations are restored.",
            "abstractedSummary": "Airport operations have resumed.",
        }
    ]

    result = calculate_news_deduction(news)
    assert result["deduction"] == 0
    assert result["reasons"] == []


def test_advisory_level_1_no_deduction():
    advisory = {
        "advisoryLevel": 1,
        "condition": "Exercise normal precautions",
        "advisory": "No major advisory risk.",
    }

    result = calculate_advisory_deduction(advisory)
    assert result["deduction"] == 0
    assert result["reasons"] == []


def test_advisory_level_2_deducts_15():
    advisory = {
        "advisoryLevel": 2,
        "condition": "Exercise increased caution",
        "advisory": "Monitor local updates.",
    }

    result = calculate_advisory_deduction(advisory)
    assert result["deduction"] == 15
    assert "Travel advisory caution" in result["reasons"]


def test_advisory_level_3_deducts_25():
    advisory = {
        "advisoryLevel": 3,
        "condition": "Reconsider travel",
        "advisory": "Affected regions may be unsafe.",
    }

    result = calculate_advisory_deduction(advisory)
    assert result["deduction"] == 25
    assert "High travel advisory risk" in result["reasons"]


def test_advisory_text_high_risk_deducts_35():
    advisory = "Do not travel due to civil unrest."
    result = calculate_advisory_deduction(advisory)
    assert result["deduction"] == 35
    assert "High travel advisory risk" in result["reasons"]


def test_get_risk_level_low():
    assert get_risk_level(80) == "Low"


def test_get_risk_level_medium():
    assert get_risk_level(60) == "Medium"


def test_get_risk_level_high():
    assert get_risk_level(40) == "High"


def test_get_condition_priority_advisory_risk():
    reasons = [
        "Weather risk",
        "High-risk news",
        "High travel advisory risk",
    ]

    result = get_condition(reasons)
    assert result == "Travel Advisory Risk"


def test_calculate_travelscore_safe_destination():
    weather = "clear sky"
    news = []
    advisory = {
        "advisoryLevel": 1,
        "condition": "Exercise normal precautions",
        "advisory": "No major issues.",
    }

    result = calculate_travelscore(weather, news, advisory)
    assert result["travelScore"] == 100
    assert result["riskLevel"] == "Low"
    assert result["condition"] == "No major safety risk"


from app.data.travelscore import (
    calculate_travelscore,
    calculate_weather_deduction,
    calculate_news_deduction,
    calculate_advisory_deduction,
    get_risk_level,
    get_condition,
)


def test_weather_no_risk_string():
    weather = "clear sky, around 25°C"
    result = calculate_weather_deduction(weather)
    assert result["deduction"] == 0
    assert result["reasons"] == []


def test_weather_heavy_rain_deducts_20():
    weather = "heavy rain expected in the afternoon"
    result = calculate_weather_deduction(weather)
    assert result["deduction"] == 20
    assert "Weather risk" in result["reasons"]


def test_weather_extreme_hot_temperature_deducts_10():
    weather = {
        "condition": "clear sky",
        "temperature": 36,
    }

    result = calculate_weather_deduction(weather)
    assert result["deduction"] == 10
    assert "Extreme temperature" in result["reasons"]


def test_weather_storm_and_extreme_temperature_deducts_30():
    weather = {
        "condition": "thunderstorm",
        "temperature": 36,
    }

    result = calculate_weather_deduction(weather)
    assert result["deduction"] == 30
    assert "Weather risk" in result["reasons"]
    assert "Extreme temperature" in result["reasons"]


def test_news_no_risk():
    news = [
        {
            "title": "Japan tourism numbers rise",
            "originalDescription": "Tourists continue to visit major attractions.",
            "abstractedSummary": "General tourism update with no safety issue.",
        }
    ]

    result = calculate_news_deduction(news)
    assert result["deduction"] == 0
    assert result["reasons"] == []


def test_news_high_risk_deducts_25():
    news = [
        {
            "title": "Earthquake causes airport disruption in Japan",
            "originalDescription": "Travellers are advised to check flights.",
            "abstractedSummary": "An earthquake has disrupted travel.",
        }
    ]

    result = calculate_news_deduction(news)
    assert result["deduction"] == 25
    assert "High-risk news" in result["reasons"]


def test_news_medium_risk_deducts_10():
    news = [
        {
            "title": "Transport strike causes delays",
            "originalDescription": "Some train services are delayed.",
            "abstractedSummary": "Transport disruption may affect travellers.",
        }
    ]

    result = calculate_news_deduction(news)
    assert result["deduction"] == 10
    assert "News risk" in result["reasons"]


def test_news_recovery_keywords_no_deduction():
    news = [
        {
            "title": "Airport reopened after storm",
            "originalDescription": "Flights have resumed and normal operations are restored.",
            "abstractedSummary": "Airport operations have resumed.",
        }
    ]

    result = calculate_news_deduction(news)
    assert result["deduction"] == 0
    assert result["reasons"] == []


def test_advisory_level_1_no_deduction():
    advisory = {
        "advisoryLevel": 1,
        "condition": "Exercise normal precautions",
        "advisory": "No major advisory risk.",
    }

    result = calculate_advisory_deduction(advisory)
    assert result["deduction"] == 0
    assert result["reasons"] == []


def test_advisory_level_2_deducts_15():
    advisory = {
        "advisoryLevel": 2,
        "condition": "Exercise increased caution",
        "advisory": "Monitor local updates.",
    }

    result = calculate_advisory_deduction(advisory)
    assert result["deduction"] == 15
    assert "Travel advisory caution" in result["reasons"]


def test_advisory_level_3_deducts_25():
    advisory = {
        "advisoryLevel": 3,
        "condition": "Reconsider travel",
        "advisory": "Affected regions may be unsafe.",
    }

    result = calculate_advisory_deduction(advisory)
    assert result["deduction"] == 25
    assert "High travel advisory risk" in result["reasons"]


def test_advisory_text_high_risk_deducts_35():
    advisory = "Do not travel due to civil unrest."
    result = calculate_advisory_deduction(advisory)
    assert result["deduction"] == 35
    assert "High travel advisory risk" in result["reasons"]


def test_get_risk_level_low():
    assert get_risk_level(80) == "Low"


def test_get_risk_level_medium():
    assert get_risk_level(60) == "Medium"


def test_get_risk_level_high():
    assert get_risk_level(40) == "High"


def test_get_condition_priority_advisory_risk():
    reasons = [
        "Weather risk",
        "High-risk news",
        "High travel advisory risk",
    ]

    result = get_condition(reasons)
    assert result == "Travel Advisory Risk"


def test_calculate_travelscore_safe_destination():
    weather = "clear sky"
    news = []
    advisory = {
        "advisoryLevel": 1,
        "condition": "Exercise normal precautions",
        "advisory": "No major issues.",
    }

    result = calculate_travelscore(weather, news, advisory)
    assert result["travelScore"] == 100
    assert result["riskLevel"] == "Low"
    assert result["condition"] == "No major safety risk"


def test_calculate_travelscore_combined_risks():
    weather = {
        "condition": "thunderstorm",
        "temperature": 36,
    }

    news = [
        {
            "title": "Earthquake causes flight cancellations",
            "originalDescription": "Airport delays reported.",
            "abstractedSummary": "Travel disruption caused by earthquake.",
        }
    ]

    advisory = {
        "advisoryLevel": 2,
        "condition": "Exercise increased caution",
        "advisory": "Monitor local warnings.",
    }

    result = calculate_travelscore(weather, news, advisory)
    # Weather 30 + news 25 + advisory 15 = 70 deduction.
    assert result["travelScore"] == 30
    assert result["riskLevel"] == "High"
    assert result["condition"] == "News Risk"