import os
import requests


# Main search query sent to World News API.
# This asks the API to find articles related to travel risks.
NEWS_FETCH_QUERY = (
    "weather OR warning OR flood OR protest OR earthquake OR airport OR flight"
)


def normalize_article(article):
    """
    Converts World News API article format into a cleaner format
    for the frontend dashboard.
    """

    return {
        "title": article.get("title", "No title available"),
        "description": article.get("summary") or article.get("text", ""),
        "url": article.get("url"),
        "source": {
            "name": article.get("source_country", "").upper()
        },
        "publishedAt": article.get("publish_date"),
    }



def get_news(news_code: str, country_name: str):
    """
    Fetches travel-risk-related news for a country.
    This function only fetches and normalizes articles.
    """

    api_key = os.getenv("WORLD_NEWS_API_KEY")

    if not api_key:
        print("World News API key is missing.")
        return []

    if not news_code:
        print(f"Missing news code for {country_name}.")
        return []

    url = "https://api.worldnewsapi.com/search-news"

    # Pass key in headers so the API key is not exposed in the URL.
    headers = {"x-api-key": api_key}

    params = {
        # source-countries = where the news source comes from, does not gaurantee
        # the article is from that country.
        # So, nlp service still needs to handle filtering to be about about that country.
        "source-countries": news_code.lower(),
        "language": "en",
        
        #Let source-countries handle the geography filter
        "text": NEWS_FETCH_QUERY,

        # Request 50 first, because some may be filtered out later.
        "number": 50,

        # Newest articles first.
        "sort": "publish-time",
        "sort-direction": "DESC",
    }

    try:
        # Pass headers explicitly alongside params
        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code != 200:
            print("World News API error:", response.status_code, response.text)
            return []

        data = response.json()
        articles = data.get("news", [])

        # Returns perfectly structured list for your NLP engine
        return [normalize_article(article) for article in articles]

    except requests.exceptions.RequestException as e:
        print(f"Network processing failed: {e}")
        return []