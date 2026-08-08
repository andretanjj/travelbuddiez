from app.database import get_connection


def search_travel_places(query: str, mode: str = "flight", limit: int = 8):
    """
    Searches TravelBuddiez autocomplete suggestions from the travel_places table.

    Modes:
    - flight: prefer city and airport rows
    - hotel: prefer city, area, station, landmark rows; airports appear lower
    """

    cleaned_query = query.strip()

    if len(cleaned_query) < 2:
        return []

    allowed_modes = {"flight", "hotel"}

    if mode not in allowed_modes:
        mode = "flight"

    exact_pattern = cleaned_query
    starts_with_pattern = f"{cleaned_query}%"
    contains_pattern = f"%{cleaned_query}%"

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                id,
                name,
                subtitle,
                code,
                city,
                country,
                country_code,
                place_type,
                provider,
                priority,

                -- Text match ranking.
                CASE
                    WHEN name ILIKE %s OR code ILIKE %s THEN 0
                    WHEN name ILIKE %s OR city ILIKE %s THEN 1
                    WHEN search_keywords ILIKE %s THEN 2
                    ELSE 3
                END AS match_rank,

                -- Different ordering for flights and hotels.
                CASE
                    WHEN %s = 'flight' AND place_type = 'city' THEN 0
                    WHEN %s = 'flight' AND place_type = 'airport' THEN 1
                    WHEN %s = 'flight' THEN 2

                    WHEN %s = 'hotel' AND place_type = 'city' THEN 0
                    WHEN %s = 'hotel' AND place_type IN ('area', 'station', 'landmark') THEN 1
                    WHEN %s = 'hotel' AND place_type = 'airport' THEN 3
                    WHEN %s = 'hotel' THEN 2

                    ELSE 2
                END AS mode_rank

            FROM travel_places
            WHERE
                name ILIKE %s
                OR city ILIKE %s
                OR country ILIKE %s
                OR code ILIKE %s
                OR search_keywords ILIKE %s
            ORDER BY
                match_rank ASC,
                mode_rank ASC,
                priority ASC,
                name ASC
            LIMIT %s;
            """,
            (
                exact_pattern,
                exact_pattern,
                starts_with_pattern,
                starts_with_pattern,
                contains_pattern,

                mode,
                mode,
                mode,
                mode,
                mode,
                mode,
                mode,

                contains_pattern,
                contains_pattern,
                contains_pattern,
                contains_pattern,
                contains_pattern,
                limit,
            ),
        )

        rows = cur.fetchall()

        suggestions = []

        for row in rows:
            suggestions.append(
                {
                    "id": str(row["id"]),
                    "name": row["name"],
                    "subtitle": row["subtitle"],
                    "code": row["code"],
                    "city": row["city"],
                    "country": row["country"],
                    "countryCode": row["country_code"],
                    "type": row["place_type"],
                    "provider": row["provider"],
                }
            )

        return suggestions

    finally:
        cur.close()
        conn.close()

def resolve_destination_airport(
    destination: str,
) -> dict | None:
    """
    Resolves a destination name or city into a suitable airport.

    Example:
    - Tokyo -> HND or NRT
    - Singapore -> SIN

    City suggestions may appear first in flight mode, so this function
    specifically returns the first airport result with an IATA code.
    """

    suggestions = search_travel_places(
        query=destination,
        mode="flight",
        limit=10,
    )

    print(
        "[TRAVEL PLACE] Suggestions for",
        destination,
        ":",
        suggestions,
    )

    # Prefer a metropolitan/city IATA code, such as TYO.
    for suggestion in suggestions:
        if (
            suggestion.get("type") == "city"
            and suggestion.get("code")
        ):
            return suggestion

    # Otherwise use an individual airport, such as HND or NRT.
    for suggestion in suggestions:
        if (
            suggestion.get("type") == "airport"
            and suggestion.get("code")
        ):
            return suggestion

    for suggestion in suggestions:
        if (
            suggestion.get("type") == "airport"
            and suggestion.get("code")
        ):
            return suggestion

    return None