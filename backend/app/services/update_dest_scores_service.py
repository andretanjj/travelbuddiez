# this updates the destination_scores and news_articles tables in the database

from app.database import get_connection
from app.services.update_destination_service import build_updated_destinations
from app.services.advisory_service import fetch_us_travel_advisories
# Used to check whether stored destination data is still fresh.
from datetime import datetime, timedelta, timezone

import logging

# Reuse Uvicorn's configured logger so messages appear in the
# VS Code terminal running the FastAPI server.
logger = logging.getLogger("uvicorn.error")

def format_embedding_for_pgvector(embedding):
    """
    Converts Python list embedding into pgvector string format.
    Eg:
    [0.1, 0.2, 0.3] -> "[0.1,0.2,0.3]"
    """

    if embedding is None:
        return None

    return "[" + ",".join(str(value) for value in embedding) + "]"


def destination_score_needs_refresh(
    last_updated,
    refresh_after_hours: int = 6,
) -> bool:
    """
    Returns True when destination dashboard data should be refreshed.

    Refresh is required when:
    1. No destination_scores row exists.
    2. last_updated is missing.
    3. The stored data is older than refresh_after_hours.

    PostgreSQL usually returns a timezone-aware datetime for TIMESTAMPTZ.
    The fallback below also handles a timezone-naive datetime safely.
    """

    if last_updated is None:
        return True

    # Convert timezone-naive database values to UTC before comparison.
    if last_updated.tzinfo is None:
        last_updated = last_updated.replace(tzinfo=timezone.utc)

    refresh_cutoff = datetime.now(timezone.utc) - timedelta(
        hours=refresh_after_hours
    )

    return last_updated < refresh_cutoff


def update_all_destinations():
    # this route manually updates all destinations in database using live data
    # only runs when this endpoint is called manually: PUT /destinations/update-all
    conn = get_connection() 
    cur = conn.cursor() 

    try:
        # countries are updated one-by-one, may take a while if there are more countries
        cur.execute("""
            SELECT
                id,
                country_code AS "countryCode",
                country_name AS country,
                city,
                news_code AS "newsCode"
            FROM destinations
            ORDER BY country_name;
        """)

        destinations = cur.fetchall()
        advisory_map = fetch_us_travel_advisories()

        updated_count = 0
        results = []

        for destination in destinations:
            updated_data = build_updated_destinations(destination, advisory_map)

            updated_score = upsert_destination_score(cur, destination["id"], updated_data)

            upsert_news_articles(cur, destination["id"], updated_data["newsArticles"])

            updated_count += 1

            results.append({
                "countryCode": destination["countryCode"],
                "country": destination["country"],
                "updatedScore": updated_score,
            })

        conn.commit()

        return {
            "updatedCount": updated_count,
            "results": results,
        }

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()


def update_one_destination(country_code: str):
    # Updates one destination.
    # Used by: PUT /destinations/{country_code}/update

    country_code = country_code.upper()

    logger.info(
        "[DESTINATION REFRESH] Loading destination metadata for %s",
        country_code,
    )

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                id,
                country_code AS "countryCode",
                country_name AS country,
                city,
                news_code AS "newsCode"
            FROM destinations
            WHERE country_code = %s;
            """,
            (country_code,),
        )

        destination = cur.fetchone()

        if destination is None:
            logger.warning(
                "[DESTINATION REFRESH] Destination %s was not found",
                country_code,
            )

            raise ValueError("Destination not found")

        logger.info(
            "[DESTINATION REFRESH] Fetching advisory, weather and news "
            "data for %s (%s)",
            destination["country"],
            country_code,
        )

        advisory_map = fetch_us_travel_advisories()

        updated_data = build_updated_destinations(
            destination,
            advisory_map,
        )

        logger.info(
            "[DESTINATION REFRESH] External data processing completed "
            "for %s. Updating destination_scores and news_articles.",
            country_code,
        )

        updated_score = upsert_destination_score(
            cur,
            destination["id"],
            updated_data,
        )

        upsert_news_articles(
            cur,
            destination["id"],
            updated_data["newsArticles"],
        )

        conn.commit()

        logger.info(
            "[DESTINATION REFRESH] Database update committed successfully "
            "for %s",
            country_code,
        )

        return updated_score

    except Exception as error:
        conn.rollback()

        logger.exception(
            "[DESTINATION REFRESH] Refresh failed for %s: %s",
            country_code,
            error,
        )

        raise

    finally:
        cur.close()
        conn.close()


def refresh_destination_if_needed(
    country_code: str,
    refresh_after_hours: int = 6,
):
    """
    Checks whether one destination has usable, fresh dashboard data.

    Database-first flow:
    1. Look up the destination and its destination_scores row.
    2. Return without calling external APIs when the data is fresh.
    3. Call update_one_destination() only when data is missing or stale.

    Returns:
        True when a refresh was performed.
        False when existing database data was still fresh.
    """

    country_code = country_code.upper()

    logger.info(
        "[DESTINATION CACHE] Checking cached dashboard data for %s",
        country_code,
    )

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                d.id,
                d.country_name AS "countryName",
                ds.id AS "scoreId",
                ds.last_updated AS "lastUpdated"
            FROM destinations d
            LEFT JOIN destination_scores ds
                ON d.id = ds.destination_id
            WHERE d.country_code = %s;
            """,
            (country_code,),
        )

        destination = cur.fetchone()

        if destination is None:
            logger.warning(
                "[DESTINATION CACHE] Destination %s does not exist "
                "in the destinations table.",
                country_code,
            )

            raise ValueError("Destination not found")

        last_updated = destination["lastUpdated"]
        score_id = destination["scoreId"]

        # A destination exists, but no destination_scores row has been created.
        if score_id is None:
            logger.info(
                "[DESTINATION CACHE] No cached score exists for %s (%s). "
                "Proceeding to fetch external APIs.",
                destination["countryName"],
                country_code,
            )

            needs_refresh = True

        # A score row exists but its last_updated value is missing.
        elif last_updated is None:
            logger.info(
                "[DESTINATION CACHE] Cached score for %s (%s) has no "
                "last_updated timestamp. Proceeding to fetch external APIs.",
                destination["countryName"],
                country_code,
            )

            needs_refresh = True

        else:
            needs_refresh = destination_score_needs_refresh(
                last_updated,
                refresh_after_hours=refresh_after_hours,
            )

            if needs_refresh:
                cache_age = datetime.now(timezone.utc) - (
                    last_updated
                    if last_updated.tzinfo is not None
                    else last_updated.replace(tzinfo=timezone.utc)
                )

                logger.info(
                    "[DESTINATION CACHE] Cached data for %s (%s) is stale. "
                    "Last updated: %s. Cache age: %.2f hours. "
                    "Proceeding to fetch external APIs.",
                    destination["countryName"],
                    country_code,
                    last_updated.isoformat(),
                    cache_age.total_seconds() / 3600,
                )

            else:
                logger.info(
                    "[DESTINATION CACHE] Cached data for %s (%s) is fresh. "
                    "Last updated: %s. Returning database results without "
                    "calling external APIs.",
                    destination["countryName"],
                    country_code,
                    last_updated.isoformat(),
                )

    finally:
        # This connection only performs a read.
        cur.close()
        conn.close()

    if not needs_refresh:
        return False

    logger.info(
        "[DESTINATION REFRESH] Starting external API refresh for %s",
        country_code,
    )

    # update_one_destination opens its own connection and transaction.
    update_one_destination(country_code)

    logger.info(
        "[DESTINATION REFRESH] External API refresh completed and cached "
        "data was updated for %s",
        country_code,
    )

    return True


def upsert_destination_score(cur, destination_id, updated_data: dict):
    # if row exists, update the data
    # if row doesnt exist, insert a new row

    cur.execute("""
        SELECT id
        FROM destination_scores
        WHERE destination_id = %s;
    """, (destination_id,))

    existing_score = cur.fetchone()

    if existing_score:
        cur.execute("""
            UPDATE destination_scores
            SET
                travel_score = %s,
                risk_level = %s,
                condition_summary = %s,
                weather_summary = %s,
                news_summary = %s,
                advisory_summary = %s,
                last_updated = NOW()
            WHERE destination_id = %s
            RETURNING *;
        """, (
            updated_data["travelScore"],
            updated_data["riskLevel"],
            updated_data["condition"],
            updated_data["weather"],
            updated_data["newsSummary"],
            updated_data["advisory"],
            destination_id,
        ))
    else:
        cur.execute("""
            INSERT INTO destination_scores (
                destination_id,
                travel_score,
                risk_level,
                condition_summary,
                weather_summary,
                news_summary,
                advisory_summary,
                last_updated
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING *;
        """, (
            destination_id,
            updated_data["travelScore"],
            updated_data["riskLevel"],
            updated_data["condition"],
            updated_data["weather"],
            updated_data["newsSummary"],
            updated_data["advisory"],
        ))

    return cur.fetchone()


def upsert_news_articles(cur, destination_id, news_articles):
    """
    Stores ranked NLP articles into news_articles table.
    For now, this stores:
        - original article info
        - Gemini relevance results
        - abstracted news summary
        - gemini embedding
    """

    if not news_articles:
        return
    
    for index, article in enumerate(news_articles, start=1):
        url = article.get("url")

        if not url:
            continue

        embedding = format_embedding_for_pgvector(article.get("embedding"))

        cur.execute("""
            INSERT INTO news_articles (
                destination_id,
                title,
                original_description,
                url,
                source_name,
                published_at,
                is_relevant,
                abstracted_summary,
                embedding,
                rank_position,
                fetched_at,
                processed_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            ON CONFLICT (destination_id, url)
            DO UPDATE SET
                title = EXCLUDED.title,
                original_description = EXCLUDED.original_description,
                source_name = EXCLUDED.source_name,
                published_at = EXCLUDED.published_at,
                is_relevant = EXCLUDED.is_relevant,
                abstracted_summary = EXCLUDED.abstracted_summary,
                embedding = EXCLUDED.embedding,
                rank_position = EXCLUDED.rank_position,
                processed_at = NOW();
        """, (
            destination_id,
            article.get("title", "No title available"),
            article.get("originalDescription"),
            url,
            article.get("sourceName"),
            article.get("publishedAt"),
            article.get("isRelevant", True),
            article.get("abstractedSummary"),
            embedding,
            index,
        ))