import os
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.database import get_connection
from app.data.destinations import DESTINATIONS
from app.services.update_destination_service import build_updated_destinations
from app.services.map_advisory_service import (
    fetch_us_travel_advisories,
    get_map_data_for_destination,
)

load_dotenv()

##debug
#print("OpenWeather key loaded:", os.getenv("OPENWEATHER_API_KEY") is not None)
#print("News key loaded:", os.getenv("WORLD_NEWS_API_KEY") is not None)
print("Database URL loaded:", os.getenv("DATABASE_URL") is not None)

app = FastAPI()

allowed_origins = [
    "http://localhost:5173",
    "https://travelbuddiez.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

## debug
""" TEST_COUNTRY_CODES = [
    "SGP",
    "IDN",
    "JPN",
] """

# Fetch advisories once when the backend starts.
# This avoids calling the advisory API every time MapView loads.
US_ADVISORY_MAP = fetch_us_travel_advisories()

@app.get("/")
def root():
    return {"message": "TravelBuddiez backend is running"}


#@app.get("/destinations")
#def get_all_destinations():
#    """
#    Used by MapView.
#
#    Returns destination data from PostgreSQL.
#    Used for map coloring and tooltip.
#    """
#    conn = get_connection()
#    cur = conn.cursor()
#
#    cur.execute("""
#        SELECT 
#            d.country_code AS "countryCode",
#            d.country_name AS country, 
#            d.city,
#            ds.travel_score AS "mapScore",
#            ds.risk_level AS "riskLevel",
#            ds.condition_summary AS condition
#        FROM destinations d
#        LEFT JOIN destination_scores ds
#        ON d.id = ds.destination_id
#        ORDER BY d.country_name;
#    """)

    # get all destinations and the latest score
    # LEFT JOIN is used so destinations still appear even if they dont have scores

#    all_destinations = cur.fetchall()

#    cur.close()
#    conn.close()

#    return all_destinations

@app.get("/destinations")
def get_all_destinations():
    """
    Used by MapView.

    Returns advisory-based mapScore for ALL countries.
    This route should be fast and cheap.
    Returns mapScore for map coloring and tooltip.
    Does NOT call weather/news APIs.
    """
    all_destinations = []

    for country_code, destination in DESTINATIONS.items():
        map_data = get_map_data_for_destination(destination, US_ADVISORY_MAP)

        all_destinations.append({
            "countryCode": destination["countryCode"],
            "country": destination["country"],
            "city": destination["city"],
            "mapScore": map_data["mapScore"],
            "riskLevel": map_data["riskLevel"],
            "condition": map_data["condition"],
        })

    return all_destinations


@app.put("/destinations/update-all")
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

            cur.execute("""
                SELECT id
                FROM destination_scores
                WHERE destination_id = %s;
            """, (destination["id"],))

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
                    destination["id"],
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
                    destination["id"],
                    updated_data["travelScore"],
                    updated_data["riskLevel"],
                    updated_data["condition"],
                    updated_data["weather"],
                    updated_data["news"],
                    updated_data["advisory"],
                ))

            updated_score = cur.fetchone()
            updated_count += 1

            results.append({
                "countryCode": destination["countryCode"],
                "country": destination["country"],
                "updatedScore": updated_score,
            })

        conn.commit()

        return {
            "message": f"{updated_count} destinations updated successfully",
            "results": results,
        }

    except Exception as error:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(error))

    finally:
        cur.close()
        conn.close()


@app.get("/destinations/{country_code}") 
def get_destination(country_code: str): 
    """ 
    Used by DestinationDashboardPage. 
    Returns detailed destination data from PostgreSQL. 
    """ 
    country_code = country_code.upper() 
    conn = get_connection() 
    cur = conn.cursor() 

    cur.execute("""
        SELECT 
            d.country_code AS "countryCode", 
            d.country_name AS country, 
            d.city, 
            ds.travel_score AS "travelScore", 
            ds.risk_level AS "riskLevel", 
            ds.condition_summary AS condition, 
            ds.weather_summary AS weather, 
            ds.news_summary AS news, 
            ds.advisory_summary AS advisory, 
            ds.last_updated AS "lastUpdated" 
        FROM destinations d 
        LEFT JOIN destination_scores ds 
        ON d.id = ds.destination_id 
        WHERE d.country_code = %s; 
    """, (country_code,)) 

    destination = cur.fetchone() 
    cur.close() 
    conn.close() 
    if destination is None: 
        raise HTTPException(status_code=404, detail="Destination not found") 
    return destination

@app.put("/destinations/{country_code}/update")
def update_destination(country_code: str):
    """
    Updates one destination using live API data.

    Flow:
    1. Get destination from PostgreSQL
    2. Fetch weather, news, and advisory data
    3. Calculate travel score
    4. Update destination_scores table
    5. Return updated destination data
    """
    country_code = country_code.upper()

    conn = get_connection()
    cur = conn.cursor()

    # basic destination info frm destinations table

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
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Destination not found")

    advisory_map = fetch_us_travel_advisories()
    updated_data = build_updated_destinations(destination, advisory_map)

    cur.execute("""
        SELECT id
        FROM destination_scores
        WHERE destination_id = %s;
    """, (destination["id"],))

    existing_score = cur.fetchone()

    # if score row esists, update with latest API data
    # if score row does not exist, create a new one

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
            destination["id"],
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
            destination["id"],
            updated_data["travelScore"],
            updated_data["riskLevel"],
            updated_data["condition"],
            updated_data["weather"],
            updated_data["news"],
            updated_data["advisory"],
        ))

    updated_score = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    return {
        "message": f"{country_code} updated successfully",
        "updatedScore": updated_score,
    }