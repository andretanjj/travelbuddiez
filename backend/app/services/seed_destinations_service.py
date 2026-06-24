from app.database import get_connection
from app.data.destinations import DESTINATIONS


def seed_destinations():
    """
    Inserts all countries from countries.geojson into the destinations table.
    This should be run manually after resetting/recreating the database.
    No external APIs are called.
    """

    conn = get_connection()
    cur = conn.cursor()

    try:
        for destination in DESTINATIONS.values():
            cur.execute("""
                INSERT INTO destinations (
                    country_code,
                    country_name,
                    city,
                    news_code,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (country_code)
                DO UPDATE SET
                    country_name = EXCLUDED.country_name,
                    city = EXCLUDED.city,
                    news_code = EXCLUDED.news_code,
                    updated_at = NOW();
            """, (
                destination["countryCode"],
                destination["country"],
                destination["city"],
                destination["newsCode"],
            ))

        conn.commit()

        return {
            "message": "Destinations seeded successfully",
            "totalCount": len(DESTINATIONS),
        }

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()