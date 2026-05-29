def calculate_travelscore(weather, news, advisory):
    score = 100
    reasons = []

    # Weather risk
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
        "rain",
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
        score -= 20
        reasons.append("Weather risk")

    if temperature is not None:
        if temperature >= 35:
            score -= 10
            reasons.append("Extremely hot weather")
        elif temperature <= 0:
            score -= 10
            reasons.append("Extremely cold weather")

    # News risk
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
        "attack",
        "riot",
        "volcano",
        "eruption",
        "landslide",
        "wildfire",
        "flood",
    ]

    medium_risk_news_keywords = [
        "protest",
        "strike",
        "smoke",
        "haze",
        "warning",
        "crashed",
        "chaos",
        "trouble",
    ]

    for article in news_articles[:5]:
        title = article.get("title", "").lower()

        if any(keyword in news_text for keyword in high_risk_news_keywords):
            score -= 25
            reasons.append("High-risk news")
        elif any(keyword in news_text for keyword in medium_risk_news_keywords):
            score -= 10
            reasons.append("News risk")
        

    # travel advisory risk
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
        score -= 35
        reasons.append("High travel advisory risk")
    elif any(keyword in advisory_text for keyword in medium_risk_advisory_keywords):
        score -= 15
        reasons.append("Travel advisory caution")

    score = max(0, min(score, 100))

    if score >= 75:
        risk_level = "Low"
    elif score >= 50:
        risk_level = "Medium"
    else:
        risk_level = "High"

    
    # if "High travel advisory risk" in reasons:
    #     condition = "Travel Advisory Risk"
    if "High-risk news" in reasons:
         condition = "News Risk"
    elif "Weather risk" in reasons:
        condition = "Weather Risk"
    # elif "Travel advisory caution" in reasons:
    #    condition = "Travel Advisory Caution"
    elif "News risk" in reasons:
         condition = "News Risk"
    else:
        condition = "No major safety risk"
    

    return {
        "travelScore": score,
        "riskLevel": risk_level,
        "condition": condition,
        "reasons": reasons,
    }