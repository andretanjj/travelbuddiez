import os
import requests


def get_news(country: str) -> str:
    api_key = os.getenv("NEWS_API_KEY")

    if api_key is None:
        return "News API key is missing."

    url = "https://newsapi.org/v2/everything"

    params = {
        "q": (
            f'"{country}" AND '
            '(travel OR tourist OR tourism OR flight OR airport OR weather OR disaster OR warning OR advisory OR safety) '
            'NOT stock NOT market NOT shares NOT currency NOT forex NOT yen NOT dollar NOT economy'
        ),
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 1,
        "apiKey": api_key,
    }

    response = requests.get(url, params=params, timeout=10)

    if response.status_code != 200:
        return "News information is currently unavailable."

    data = response.json()
    articles = data.get("articles", [])

    if len(articles) == 0:
        return "No major travel-related news found."

    article = articles[0]
    title = article.get("title", "No title available")

    return title