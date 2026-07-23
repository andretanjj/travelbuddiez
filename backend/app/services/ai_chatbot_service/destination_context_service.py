from typing import Any
import re

from app.database import get_connection


def get_available_destinations() -> list[dict[str, str | None]]:
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                country_code,
                country_name,
                city
            FROM destinations
            ORDER BY country_name;
            """
        )

        rows = cur.fetchall()

        return [
            {
                "country_code": row["country_code"],
                "country_name": row["country_name"],
                "city": row["city"],
            }
            for row in rows
        ]

    finally:
        cur.close()
        conn.close()


def contains_complete_phrase(
    message: str,
    phrase: str,
) -> bool:
    """
    Matches a complete country name, city name, or country code.

    Examples:
    - 'Japan' matches 'Is Japan safe?'
    - 'ARE' does not match the word 'are'
    - 'Singapore' does not match an unrelated longer word
    """
    pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"

    return re.search(
        pattern,
        message,
        flags=re.IGNORECASE,
    ) is not None


def detect_destination_codes(message: str) -> list[str]:
    destinations = get_available_destinations()
    detected_codes: list[str] = []

    for destination in destinations:
        country_code = destination["country_code"]
        country_name = destination["country_name"]
        city = destination["city"]

        possible_names = [
            country_name,
            city,
        ]

        name_found = any(
            name and contains_complete_phrase(message, name)
            for name in possible_names
        )

        if (
            name_found
            and country_code not in detected_codes
        ):
            detected_codes.append(country_code)

    return detected_codes


def get_destination_context(
    country_codes: list[str],
) -> list[dict[str, Any]]:
    if not country_codes:
        return []

    conn = get_connection()
    cur = conn.cursor()

    try:
        placeholders = ", ".join(["%s"] * len(country_codes))

        query = f"""
            SELECT
                d.country_code,
                d.country_name,
                d.city,
                ds.travel_score,
                ds.risk_level,
                ds.condition_summary,
                ds.weather_summary,
                ds.news_summary,
                ds.advisory_summary,
                ds.last_updated
            FROM destinations d
            LEFT JOIN destination_scores ds
                ON ds.destination_id = d.id
            WHERE d.country_code IN ({placeholders})
            ORDER BY d.country_name;
        """

        cur.execute(query, tuple(country_codes))
        rows = cur.fetchall()

        return [
            {
                "country_code": row["country_code"],
                "country_name": row["country_name"],
                "city": row["city"],
                "travel_score": row["travel_score"],
                "risk_level": row["risk_level"],
                "condition_summary": row["condition_summary"],
                "weather_summary": row["weather_summary"],
                "news_summary": row["news_summary"],
                "advisory_summary": row["advisory_summary"],
                "last_updated": (
                    row["last_updated"].isoformat()
                    if row["last_updated"]
                    else None
                ),
            }
            for row in rows
        ]

    finally:
        cur.close()
        conn.close()

def get_recommendation_candidates(
    limit: int = 10,
) -> list[dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                d.country_code,
                d.country_name,
                d.city,
                ds.travel_score,
                ds.risk_level,
                ds.condition_summary,
                ds.weather_summary,
                ds.news_summary,
                ds.advisory_summary,
                ds.last_updated
            FROM destinations d
            INNER JOIN destination_scores ds
                ON ds.destination_id = d.id
            WHERE ds.travel_score IS NOT NULL
            ORDER BY ds.travel_score DESC
            LIMIT %s;
            """,
            (limit,),
        )

        rows = cur.fetchall()

        return [
            {
                "country_code": row["country_code"],
                "country_name": row["country_name"],
                "city": row["city"],
                "travel_score": row["travel_score"],
                "risk_level": row["risk_level"],
                "condition_summary": row["condition_summary"],
                "weather_summary": row["weather_summary"],
                "news_summary": row["news_summary"],
                "advisory_summary": row["advisory_summary"],
                "last_updated": (
                    row["last_updated"].isoformat()
                    if row["last_updated"]
                    else None
                ),
            }
            for row in rows
        ]

    finally:
        cur.close()
        conn.close()