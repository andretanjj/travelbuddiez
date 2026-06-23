# this updates the map_advisory table in the database

from app.database import get_connection
from app.services.map_advisory_service import (
    fetch_us_travel_advisories,
    get_map_data_for_destination,
)

def update_map_advisories():
    
    # updates map_advisories table in database using the RSS feed
    # this is used for the colouring of the map and the map tooltip

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT
                id, 
                country_code AS "countryCode",
                country_name AS country,
                city
            FROM destinations
            ORDER BY country_name;
        """)

        destinations = cur.fetchall()

        US_ADVISORY_MAP = fetch_us_travel_advisories()

        updated_count = 0

        for destination in destinations:
            map_data = get_map_data_for_destination(destination, US_ADVISORY_MAP)

            cur.execute("""
                SELECT id
                FROM map_advisories
                WHERE destination_id = %s;
            """, (destination["id"],))

            existing_row = cur.fetchone()

            if existing_row:
                cur.execute("""
                    UPDATE map_advisories
                    SET
                        map_score = %s,
                        risk_level = %s,
                        condition_summary = %s,
                        source = %s,
                        last_updated = NOW()
                    WHERE destination_id = %s
                """, (
                    map_data["mapScore"],
                    map_data["riskLevel"],
                    map_data["condition"],
                    "US Travel Advisory",
                    destination_id,
                ))
            else:
                cur.execute("""
                    INSERT INTO map_advisories(
                        destination_id,
                        map_score,
                        risk_level,
                        condition_summary,
                        source,
                        last_updated
                    )
                    VALUES (%s, %s, %s, %s, %s, NOW());
                """, (
                    destination["id"],
                    map_data["mapScore"],
                    map_data["riskLevel"],
                    map_data["condition"],
                    "US Travel Advisory"
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

