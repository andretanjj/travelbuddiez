def calculate_travelscore(weather, news, advisory):
    score = 100
    reasons = []

    weather_deduction = calculate_weather_deduction(weather)
    score -= weather_deduction["deduction"]
    reasons.extend(weather_deduction["reasons"])

    news_deduction = calculate_news_deduction(news)
    score -= news_deduction["deduction"]
    reasons.extend(news_deduction["reasons"])

    advisory_deduction = calculate_advisory_deduction(advisory)
    score -= advisory_deduction["deduction"]
    reasons.extend(advisory_deduction["reasons"])

    score = max(0, min(score, 100))

    return {
        "travelScore": score,
        "riskLevel": get_risk_level(score),
        "condition": get_condition(reasons),
    }


def calculate_weather_deduction(weather):
    deduction = 0
    reasons = []

    weather_condition = ""
    temperature = None

    if isinstance(weather, dict):
        weather_condition = str(
            weather.get("condition")
            or weather.get("Condition")
            or weather.get("description")
            or ""
        ).lower()

        temperature = (
            weather.get("temperature")
            or weather.get("Temperature")
            or weather.get("temp")
        )

    elif isinstance(weather, str):
        weather_condition = weather.lower()

    bad_weather_keywords = [
        "heavy rain",
        "thunderstorm",
        "storm",
        "typhoon",
        "haze",
        "smoke",
        "flood",
        "snow",
        "extreme heat",
    ]

    if any(keyword in weather_condition for keyword in bad_weather_keywords):
        deduction += 20
        reasons.append("Weather risk")

    if temperature is not None:
        if temperature >= 35:
            deduction += 10
            reasons.append("Extreme temperature")
        elif temperature <= 0:
            deduction += 10
            reasons.append("Extreme temperature")

    return {
        "deduction": deduction,
        "reasons": reasons,
    }


def calculate_news_deduction(news):
    deduction = 0
    reasons = []

    news_articles = []

    if isinstance(news, dict):
        news_articles = news.get("articles", [])
    elif isinstance(news, list):
        news_articles = news

    high_risk_news_keywords = [
        "earthquake",
        "tsunami",
        "war",
        "terror",
        "terrorism",
        "attack",
        "riot",
        "volcano",
        "eruption",
        "landslide",
        "wildfire",
        "flood",
        "flooding",
        "evacuation",
        "emergency",
        "disaster",
        "typhoon",
        "cyclone",
        "hurricane",
        "airport closed",
        "flight cancelled",
        "state of emergency",
    ]

    medium_risk_news_keywords = [
        "protest",
        "strike",
        "smoke",
        "haze",
        "warning",
        "alert",
        "advisory",
        "delay",
        "cancelled",
        "disruption",
        "unrest",
        "demonstration",
        "heavy rain",
        "heatwave",
        "storm",
    ]

    high_risk_found = False
    medium_risk_found = False

    for article in news_articles[:5]:
        title = article.get("title", "")
        description = article.get("description", "")
        content = article.get("content", "")

        news_text = f"{title} {description} {content}".lower()

        if any(keyword in news_text for keyword in high_risk_news_keywords):
            high_risk_found = True

        elif any(keyword in news_text for keyword in medium_risk_news_keywords):
            medium_risk_found = True

    if high_risk_found:
        deduction += 25
        reasons.append("High-risk news")
    elif medium_risk_found:
        deduction += 10
        reasons.append("News risk")

    return {
        "deduction": deduction,
        "reasons": reasons,
    }


def calculate_advisory_deduction(advisory):
    deduction = 0
    reasons = []

    advisory_text = str(advisory).lower()

    high_risk_advisory_keywords = [
        "avoid travel",
        "do not travel",
        "natural disaster",
        "disaster warning",
        "affected regions",
        "terrorism",
        "civil unrest",
    ]

    medium_risk_advisory_keywords = [
        "exercise caution",
        "monitor",
        "check",
        "warning",
        "regional travel notices",
        "travel notices",
    ]

    if any(keyword in advisory_text for keyword in high_risk_advisory_keywords):
        deduction += 35
        reasons.append("High travel advisory risk")

    elif any(keyword in advisory_text for keyword in medium_risk_advisory_keywords):
        deduction += 15
        reasons.append("Travel advisory caution")

    return {
        "deduction": deduction,
        "reasons": reasons,
    }


def get_risk_level(score):
    if score >= 75:
        return "Low"
    elif score >= 50:
        return "Medium"
    else:
        return "High"


def get_condition(reasons):
    if "High travel advisory risk" in reasons:
        return "Travel Advisory Risk"
    elif "High-risk news" in reasons:
        return "News Risk"
    elif "Weather risk" in reasons:
        return "Weather Risk"
    elif "Travel advisory caution" in reasons:
        return "Travel Advisory Caution"
    elif "News risk" in reasons:
        return "News Risk"
    elif "Extreme temperature" in reasons:
        return "Weather Risk"
    else:
        return "No major safety risk"