from app.services.weather_service import get_weather
from app.services.news_service import get_news
from app.services.advisory_service import get_advisory
from app.services.map_advisory_service import (
    fetch_us_travel_advisories,
    get_map_data_for_destination,
)
from app.data.travelscore import calculate_travelscore

# convert news_service.py output into a text summary for storing in PostgreSQL
def summarise_news(news_articles):
    if not news_articles:
        return "No major travel-related news found."

    titles = []

    for article in news_articles:
        title = article.get("title")

        if title:
            titles.append(title)

    if not titles:
        return "No major travel-related news found."

    return " | ".join(titles)

def build_updated_destinations(destination: dict, advisory_map: dict):
    weather = get_weather(destination["city"])
    news_articles = get_news(destination["countryCode"], destination["country"])

    advisory_data = get_map_data_for_destination(destination, advisory_map)

    news_summary = summarise_news(news_articles)

    score_data = calculate_travelscore(
        weather = weather,
        news = news_summary,
        advisory = advisory_data,
    )

    return {
        "weather": weather,
        "news": news_summary,
        "advisory": advisory_data["condition"],
        "travelScore": score_data["travelScore"],
        "riskLevel": score_data["riskLevel"],
        "condition": score_data["condition"],
    }