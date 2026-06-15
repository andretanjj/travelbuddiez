import math
import os
import re
import json
import requests

"""
Flow
1. World News API returns 50 articles

2. Python hard filter:
    - remove duplicate articles
    - destination must be mentioned
    - remove obvious sports/finance/etc.

3. Gemini Flash batch abstraction/classification:
    - one generateContent containing up to 30 candidate articles
    - returns index, isRelevant, abstractedSummary

4. Gemini Embedding batch
    - embed only articles where isRelevant == true
    - use abstractedSummary as the embedding text

5. Cosine similarity
    - compare abstractedSummary embedding against ARTICLES_RELEVANCE_QUERY

6. Return top 10
"""

GEMINI_FLASH_MODEL = "gemini-3.1-flash-lite"
GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"


GEMINI_FLASH_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    + GEMINI_FLASH_MODEL
    + ":generateContent"
)

GEMINI_BATCH_EMBEDDING_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    + GEMINI_EMBEDDING_MODEL
    + ":batchEmbedContents"
)

# Use 768 dimensions for easier/cheaper future pgvector storage.
# Later database column:
# embedding VECTOR(768)
OUTPUT_DIMENSIONALITY = 768

MIN_SIMILARITY_SCORE = 0.45

# Maximum number of articles passed to Gemini Flash in one call.
MAX_ARTICLES_TO_ABSTRACT = 30

# For semantic embeddings.
ARTICLE_RELEVANCE_QUERY = (
    "destination travel safety and travel suitability for tourists including weather warnings, "
    "natural disasters, earthquakes, typhoons, floods, storms, airport delays, "
    "flight cancellations, transport disruption, protests, unrest, emergency alerts, "
    "travel advisories, border restrictions, health warnings, crime affecting travellers, "
    "airport reopening, transport resuming, restrictions eased, advisory level lowered"
)

# First-level filtering:
# Article must mention the clicked destination or one of its major related places.
DESTINATION_ALIASES = {
    "SGP": ["singapore"],
    "IDN": ["indonesia", "jakarta", "bali"],
    "JPN": ["japan", "tokyo", "osaka", "kyoto", "hokkaido", "okinawa"],
}

# temp cache while backend is running.
# Avoids repeated Gemini calls for the same text during local testing.
EMBEDDING_CACHE = {}


FLASH_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "articles": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {
                        "type": "integer"
                    },
                    "isRelevant": {
                        "type": "boolean"
                    },
                    "abstractedSummary": {
                        "type": "string"
                    }
                },
                "required": [
                    "index",
                    "isRelevant",
                    "abstractedSummary"
                ]
            }
        }
    },
    "required": [
        "articles"
    ]
}


def load_news_keywords():
    """
    Loads keyword rules from:
    backend/app/data/news_keywords.json

    Only use irrelevant keywords for cheap hard filtering.
    """

    current_dir = os.path.dirname(__file__)

    keyword_path = os.path.join(
        current_dir,
        "..",
        "data",
        "news_keywords.json",
    )

    with open(keyword_path, "r") as file:
        return json.load(file)
    

KEYWORDS = load_news_keywords()
IRRELEVANT_KEYWORDS = KEYWORDS["irrelevant_keywords"]
    

def article_to_text(article):
    """
    Converts one article into clean text
    Use only title + description.
    DO NOT use full webpage because it may contain ads, sidebars, etc.
    """

    title = article.get("title", "") or ""
    description = article.get("description", "") or ""

    return f"{title}. {description}".strip()


def contains_phrase(text, phrase):
    """
    Checks whether a phrase appears properly in text.

    This avoids matching tiny partial words accidentally.
    Example:
    - "rain" should not automatically match "rainfall"
    """

    pattern = r"\b" + re.escape(phrase.lower()) + r"\b"
    return re.search(pattern, text.lower()) is not None


def has_keyword(article, keywords):
    """
    Returns True if the article contains at least one keyword.

    Here, this is only used to remove obvious irrelevant articles
    like sports, finance, entertainment, etc.
    """

    text = article_to_text(article).lower()

    for keyword in keywords:
        if contains_phrase(text, keyword):
            return True

    return False


def get_candidates(articles, country_code):
    """
    Cheap filtering before Gemini embeddings.

    This should NOT be too strict.

    Hard filters:
    1. Remove duplicates
    2. Article must mention destination/city alias
    3. Remove obvious irrelevant topics like sports/finance

    IMPT:
    - Do not require travel-risk keywords here.
    Gemini Flash will decide whether the article is travel-safety relevant.
    """

    seen = set()
    candidates = []

    aliases = DESTINATION_ALIASES.get(country_code.upper(), []) if country_code else []

    for article in articles:
        title = article.get("title", "") or ""
        url = article.get("url", "") or ""
        text = article_to_text(article).lower()

        # Remove duplicates by URL first, otherwise title.
        duplicate_key = url if url else title.lower()

        if duplicate_key in seen:
            continue

        seen.add(duplicate_key)

        # Hard filter 1:
        # If country has aliases, article must mention one alias
        # If country has no aliases: do not check destination match, skip hard filter 1
        if aliases:
            is_related = False

            for alias in aliases:
                if contains_phrase(text, alias):
                    is_related = True
                    break

            if not is_related:
                continue

        # Hard filter 2:
        # Remove obvious irrelevant topics before Gemini call.
        if has_keyword(article, IRRELEVANT_KEYWORDS):
            continue

        candidates.append(article.copy())

    return candidates[:MAX_ARTICLES_TO_ABSTRACT]


def abstract_articles_with_gemini(candidates, country_code):
    """
    Uses Gemini Flash to classify and abstract all candidate articles in one call.

    For each article, Gemini returns:
    - index
    - isRelevant
    - abstractedSummary

    Only isRelevant=True articles are passed to the embedding stage.

    Future database fields:
    - is_relevant
    - abstracted_summary
    - embedding
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if api_key is None:
        print("Gemini API key is missing.")
        return []

    article_blocks = []

    for index, article in enumerate(candidates):
        title = article.get("title", "") or ""
        description = article.get("description", "") or ""

        article_blocks.append(
            f"""
Article {index}
Title: {title}
Description: {description}
"""
        )

    prompt = f"""
You are helping TravelBuddiez classify news for a travel safety dashboard.

Clicked destination country code: {country_code}

For each article:
1. Decide whether it is relevant to destination-specific travel safety, travel disruption, or travel suitability, including both risks and improvements.
2. If relevant, write one concise neutral summary focused on travel impact.
3. If not relevant, set isRelevant to false and abstractedSummary to an empty string.

Relevant topics include:
- weather risks
- natural disasters
- airport or flight disruption
- transport disruption
- protests or civil unrest
- conflict or security risk
- health risk
- travel advisory
- border restriction
- crime or safety issues affecting travellers
- general travel conditions that may affect tourists
- recovery or improvement updates that affect travellers, such as airport reopening, transport resuming, advisory level lowered, restrictions eased

Not relevant topics include:
- sports
- finance, stocks, currency, interest rates
- entertainment
- culture
- technology
- general politics with no travel impact
- articles about another country only

Rules:
- Return JSON only.
- Keep the same index as the input article.
- Do not invent facts.
- The abstractedSummary must be based only on the given title and description.
- The abstractedSummary should be one sentence.
- If unsure, mark isRelevant as false.

Articles:
{''.join(article_blocks)}
"""

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 8192,
            "responseMimeType": "application/json",
            "responseJsonSchema": FLASH_RESPONSE_SCHEMA
        }
    }

    response = requests.post(
        GEMINI_FLASH_URL,
        headers=headers,
        json=payload,
        timeout=40,
    )

    if response.status_code != 200:
        print("Gemini Flash abstraction error:", response.status_code, response.text)
        return []

    data = response.json()

    try:
        response_text = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed_response = json.loads(response_text)
        classifications = parsed_response.get("articles", [])
        print("\n--- Gemini isRelevant Debug ---")

        for item in classifications:
            index = item.get("index")
            is_relevant = item.get("isRelevant", False)

            if index is None:
                continue

            if index < 0 or index >= len(candidates):
                continue

            print("Title:", candidates[index].get("title"))
            print("isRelevant:", is_relevant)
            print("-" * 50)

    except Exception as error:
        print("Failed to parse Gemini Flash abstraction response:", error)
        print("Raw Gemini response:", data)
        return []

    abstracted_articles = []

    for item in classifications:
        index = item.get("index")
        is_relevant = item.get("isRelevant", False)
        abstracted_summary = item.get("abstractedSummary", "") or ""

        if index is None:
            continue

        if index < 0 or index >= len(candidates):
            continue

        if not is_relevant:
            continue

        # If Gemini says relevant but summary is empty, skip it.
        # This keeps the embedding stage clean.
        if not abstracted_summary.strip():
            continue

        article = candidates[index].copy()

        # Store AI-produced fields.
        article["isRelevant"] = True
        article["abstractedSummary"] = abstracted_summary.strip()

        # Preserve the original API description for future database storage.
        article["originalDescription"] = article.get("description", "") or ""

        # Practical frontend choice:
        # If your dashboard displays article.description, this makes it show the AI summary.
        article["description"] = article["abstractedSummary"]

        abstracted_articles.append(article)

    return abstracted_articles


def get_gemini_embeddings_batch(text_items):
    """
    Sends query + articles to Gemini in one batch request.

    text_items format:
    [
        {
            "text": "...",
            "taskType": "RETRIEVAL_QUERY" or "RETRIEVAL_DOCUMENT",
            "title": "optional title"
        }
    ]

    Returns a list of embeddings in the same order.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if api_key is None:
        print("Gemini API key is missing.")
        return None

    embeddings = [None] * len(text_items)
    requests_to_send = []
    positions_to_fill = []

    for index, item in enumerate(text_items):
        text = item["text"]
        task_type = item["taskType"]
        title = item.get("title", "")

        cache_key = f"{task_type}:{OUTPUT_DIMENSIONALITY}:{title}:{text}"

        if cache_key in EMBEDDING_CACHE:
            embeddings[index] = EMBEDDING_CACHE[cache_key]
            continue

        config = {
            "taskType": task_type,
            "outputDimensionality": OUTPUT_DIMENSIONALITY,
        }

        # Title only helps document retrieval, not query embedding.
        if title and task_type == "RETRIEVAL_DOCUMENT":
            config["title"] = title

        request_item = {
            "model": "models/" + GEMINI_EMBEDDING_MODEL,
            "content": {
                "parts": [
                    {
                        "text": text
                    }
                ]
            },
            "embedContentConfig": config,
        }

        requests_to_send.append(request_item)
        positions_to_fill.append({
            "index": index,
            "cacheKey": cache_key,
        })

    # Everything was already cached.
    if not requests_to_send:
        return embeddings

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }

    payload = {
        "requests": requests_to_send
    }

    response = requests.post(
        GEMINI_BATCH_EMBEDDING_URL,
        headers=headers,
        json=payload,
        timeout=30,
    )

    if response.status_code != 200:
        print("Gemini batch embedding error:", response.status_code, response.text)
        return None

    data = response.json()

    try:
        returned_embeddings = data["embeddings"]

        for returned_embedding, position in zip(returned_embeddings, positions_to_fill):
            vector = returned_embedding["values"]

            original_index = position["index"]
            cache_key = position["cacheKey"]

            embeddings[original_index] = vector
            EMBEDDING_CACHE[cache_key] = vector

        return embeddings

    except KeyError:
        print("Unexpected Gemini batch embedding response:", data)
        return None


def cosine_similarity(vector_a, vector_b):
    """
    Calculates cosine similarity manually.

    Higher score means the article is more semantically similar
    to the TravelBuddiez relevance query.
    """
    dot_product = 0
    magnitude_a = 0
    magnitude_b = 0

    for a, b in zip(vector_a, vector_b):
        dot_product += a * b
        magnitude_a += a * a
        magnitude_b += b * b

    if magnitude_a == 0 or magnitude_b == 0:
        return 0

    return dot_product / (math.sqrt(magnitude_a) * math.sqrt(magnitude_b))


def rank_news_articles(articles, country_code=None, top_k=10):
    """
        Flow:
        1. Cheap hard filtering
        2. Gemini Flash abstraction/classification
        3. Gemini batch embeddings for isRelevant=True summaries
        4. Cosine similarity
        5. Minimum similarity threshold
        6. Return top relevant articles

        Later database flow:
        - Store title, url, originalDescription, abstractedSummary, isRelevant
        - Store embedding vector in pgvector
        - Use pgvector cosine search instead of recalculating every click
    """

    if not articles:
        return []
    
    # 1. Cheap hard filtering
    candidates = get_candidates(articles, country_code)

    print("\n--- Candidate Articles Before Gemini ---")
    print("Original article count:", len(articles))
    print("Candidate article count:", len(candidates))

    if not candidates:
        return []
    
    # 2: one Gemini Flash call for all candidate articles.
    abstracted_articles = abstract_articles_with_gemini(
        candidates,
        country_code,
    )
    
    print("\n--- Articles After Gemini Flash Abstraction ---")
    print("Relevant abstracted article count:", len(abstracted_articles))


    if not abstracted_articles:
        return []
    
    # 3. Gemini embedding batch call.
    # First item is the query, remaining items are relevant article summaries.
    text_items = [
        {
            "text": ARTICLE_RELEVANCE_QUERY,
            "taskType": "RETRIEVAL_QUERY",
        }
    ]

    for article in abstracted_articles:
        text_items.append({
            "text": article["abstractedSummary"],
            "taskType": "RETRIEVAL_DOCUMENT",
            "title": article.get("title", ""),
        })

    embeddings = get_gemini_embeddings_batch(text_items)

    if embeddings is None:
        return []

    query_embedding = embeddings[0]
    article_embeddings = embeddings[1:]

    ranked_articles = []

    # 4. cosine similarity
    for article, article_embedding in zip(abstracted_articles, article_embeddings):
        if article_embedding is None:
            continue

        similarity_score = cosine_similarity(
            query_embedding,
            article_embedding,
        )

        ranked_article = article.copy()
        ranked_article["similarityScore"] = round(float(similarity_score), 4)
        ranked_article["rankingMethod"] = "flash_abstraction_gemini_embedding_cosine"

        # Do NOT return the full embedding to frontend.
        # Later store embedding in Supabase PostgresSQL using pgvector.
        ranked_articles.append(ranked_article)

    ranked_articles.sort(
        key=lambda article: article["similarityScore"],
        reverse=True,
    )

    print("\n--- Final Article Ranking Debug ---")

    for article in ranked_articles:
        print("Title:", article.get("title", "No title"))
        print("Similarity Score:", article.get("similarityScore"))
        print("Abstracted Summary:", article.get("abstractedSummary"))
        print("-" * 50)

    #5. apply minimum similarity threshold
    relevant_articles = []

    for article in ranked_articles:
        if article["similarityScore"] >= MIN_SIMILARITY_SCORE:
            relevant_articles.append(article)

    return relevant_articles[:top_k]