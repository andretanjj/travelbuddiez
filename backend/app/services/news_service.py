import os
import requests


# Main search query sent to World News API.
# This asks the API to find articles related to travel risks.
TRAVEL_RISK_QUERY = (
    "weather OR warning OR airport OR flood OR protest OR earthquake OR flight"
)


HIGH_RISK_KEYWORDS = [
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
    "state of emergency",
]

MEDIUM_RISK_KEYWORDS = [
    "protest",
    "strike",
    "haze",
    "smoke",
    "thunderstorm",
    "storm",
    "heavy rain",
    "heatwave",
    "warning",
    "alert",
    "advisory",
    "unrest",
    "demonstration",
]

TRAVEL_DISRUPTION_KEYWORDS = [
    "airport",
    "flight",
    "flights",
    "airline",
    "travel",
    "tourist",
    "tourists",
    "border",
    "visa",
]

DISRUPTION_KEYWORDS = [
    "cancelled",
    "canceled",
    "delayed",
    "delay",
    "closed",
    "closure",
    "suspended",
    "disrupted",
    "disruption",
    "stranded",
    "removed from flight",
]

IRRELEVANT_KEYWORDS = [
    "stock",
    "market",
    "shares",
    "currency",
    "forex",
    "earnings",
    "profit",
    "football",
    "basketball",
    "motogp",
    "motorcycling",
    "celebrity",
    "research",
    "academic",
    "election",
    "senate",
]


def article_to_text(article):
    """
    Combines article title, summary, and text into one lowercase string
    so we can check it against irrelevant keywords.
    """

    title = article.get("title", "") or ""
    summary = article.get("summary", "") or ""
    text = article.get("text", "") or ""

    return f"{title} {summary} {text}".lower()


def is_relevant(article):
    article_text = article_to_text(article)

    has_irrelevant_keyword = any(
        keyword in article_text
        for keyword in IRRELEVANT_KEYWORDS
    )

    if has_irrelevant_keyword:
        return False

    has_high_risk_keyword = any(
        keyword in article_text
        for keyword in HIGH_RISK_KEYWORDS
    )

    has_medium_risk_keyword = any(
        keyword in article_text
        for keyword in MEDIUM_RISK_KEYWORDS
    )

    has_travel_context = any(
        keyword in article_text
        for keyword in TRAVEL_DISRUPTION_KEYWORDS
    )

    has_disruption = any(
        keyword in article_text
        for keyword in DISRUPTION_KEYWORDS
    )

    return (
        has_high_risk_keyword
        or has_medium_risk_keyword
        or (has_travel_context and has_disruption)
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

def article_mentions_country(article, country_name):
    article_text = article_to_text(article)
    return country_name.lower() in article_text


def get_news(news_code: str, country_name: str):
    """
    Fetches travel-risk-related news for a country.

    Steps:
    1. Request 20 articles from World News API using TRAVEL_RISK_QUERY.
    2. Remove articles with irrelevant keywords.
    3. Return the first 5 cleaned articles.
    """

    api_key = os.getenv("WORLD_NEWS_API_KEY")

    if api_key is None:
        print("World News API key is missing.")
        return []

    if not news_code:
        print(f"Missing news code for {country_name}.")
        return []

    url = "https://api.worldnewsapi.com/search-news"

    params = {
        "api-key": api_key,
        "source-country": news_code.lower(),
        "language": "en",
        "text": f"{country_name} {TRAVEL_RISK_QUERY}",


        # Request 20 first, because some may be filtered out later.
        "number": 20,

        # Newest articles first.
        "sort": "publish-time",
        "sort-direction": "DESC",
    }

    response = requests.get(url, params=params, timeout=10)

    if response.status_code != 200:
        print("World News API error:", response.status_code, response.text)
        return []

    data = response.json()

    # WorldNewsAPI stores returned articles in the "news" field.
    articles = data.get("news", [])

    # Remove irrelevant articles after the API search.
    cleaned_articles = [
        article for article in articles
        if article_mentions_country(article, country_name)
        and is_relevant(article)
    ]

    top_5_articles = cleaned_articles[:5]

    #debug
    print(f"\nNews debug for {country_name} ({news_code})")
    print("All news titles:")
    for article in articles:
        print("-", article.get("title"))

    print("\nTop 5 cleaned news titles:")
    for article in top_5_articles:
        print("-", article.get("title"))

    # Return only the top 5 after filtering.
    return [
        normalize_article(article)
        for article in top_5_articles
    ]