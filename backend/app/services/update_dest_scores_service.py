# this updates the destination_scores table in the database

from app.database import get_connection
from app.services.update_destination_service import build_updated_destinations
from app.services.map_advisory_service import fetch_us_travel_advisories

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
                city
            FROM destinations
            ORDER BY country_name;
        """)

        destinations = cur.fetchall()
        advisory_map = fetch_us_travel_advisories()

        updated_count = 0
        results = []

        for destination in destinations:
            updated_data = build_updated_destinations(destination, advisory_map)

            updated_score = upsert_destination_score(
                cur,
                destination["id"],
                updated_data,
            )

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
    # updates for 1 destination
    # used by: PUT /destinations/{country_code}/update

    country_code = country_code.upper() 
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
            WHERE country_code = %s;
        """, (country_code,))

        destination = cur.fetchone()

        if destination is None:
            raise ValueError("Destination not found")

        advisory_map = fetch_us_travel_advisories()
        updated_data = build_updated_destinations(destination, advisory_map)

        updated_score = upsert_destination_score(
            cur,
            destination["id"],
            updated_data,
        )

        conn.commit()
        return updated_score

    except Exception as error:
        conn.rollback()
        raise error

    finally:
        cur.close()
        conn.close()

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
            updated_data["news"],
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
            updated_data["news"],
            updated_data["advisory"],
        ))

    return cur.fetchone()