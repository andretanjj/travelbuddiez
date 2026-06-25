# this updates the destination_map_scores table in the database

from app.database import get_connection
from app.services.advisory_service import (
    fetch_us_travel_advisories,
    get_advisory_data_for_destination,
)

def update_map_scores():
    
    """
    Updates destination_map_scores table using US travel advisory data.
    This is used by map polygon coloring and country tooltip.
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
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

        for destination in destinations:
            advisory_data = get_advisory_data_for_destination(destination, advisory_map)

            cur.execute("""
                INSERT INTO destination_map_scores (
                    destination_id,
                    country_code,
                    country_name,
                    map_score,
                    risk_level,
                    condition_summary,
                    advisory_level,
                    advisory_summary,
                    source,
                    last_updated
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (destination_id)
                DO UPDATE SET
                    country_code = EXCLUDED.country_code,
                    country_name = EXCLUDED.country_name,
                    map_score = EXCLUDED.map_score,
                    risk_level = EXCLUDED.risk_level,
                    condition_summary = EXCLUDED.condition_summary,
                    advisory_level = EXCLUDED.advisory_level,
                    advisory_summary = EXCLUDED.advisory_summary,
                    source = EXCLUDED.source,
                    last_updated = NOW();
            """, (
                destination["id"],
                destination["countryCode"],
                destination["country"],
                advisory_data["mapScore"],
                advisory_data["riskLevel"],
                advisory_data["condition"],
                advisory_data["advisoryLevel"],
                advisory_data["advisory"],
                "US Travel Advisory",
            ))
            updated_count += 1

        conn.commit()
        return updated_count

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()

