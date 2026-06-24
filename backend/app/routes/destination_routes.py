from fastapi import APIRouter, HTTPException

from app.database import get_connection
from app.services.seed_destinations_service import seed_destinations
from app.services.update_dest_scores_service import (
    update_all_destinations,
    update_one_destination
)
from app.services.update_map_scores_service import update_map_scores


router = APIRouter(
    prefix="/destinations",
    tags=["destinations"],
)

@router.put("/seed")
def seed_all_destinations():
    """
    Manually inserts countries from countries.geojson into the destinations table.
    Run this after resetting/recreating the database.
    """

    try:
        seed_result = seed_destinations()

        return {
            "message": "Destinations seeded successfully",
            "result": seed_result,
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
    

@router.put("/map-scores/update-all")
def update_all_map_scores():
    """
    Manually updates map scores using US travel advisory data.
    Used for map coloring and tooltip data.
    """

    try:
        updated_count = update_map_scores()

        return {
            "message": f"{updated_count} map scores updated successfully"
        }
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.get("")
def get_all_destinations():
    """
    Used by MapView
    Returns mapScore for map coloring and tooltip.
    Does NOT call weather/news/Gemini APIs.
    returns data frm database
    """
    conn = get_connection()
    cur = conn.cursor()

    try: 
        cur.execute("""
            SELECT
                d.country_code AS "countryCode",
                d.country_name AS country,
                d.city,
                dms.map_score AS "mapScore",
                dms.risk_level AS "riskLevel",
                dms.condition_summary AS condition,
                dms.last_updated AS "lastUpdated"
            FROM destinations d
            LEFT JOIN destination_map_scores dms
            ON d.id = dms.destination_id
            ORDER BY d.country_name;
        """)

        return cur.fetchall()
    
    finally:
        cur.close()
        conn.close()


@router.put("/update-all")
def update_every_destinations():
    # this route manually updates all destinations in database using live data
    # only runs when this endpoint is called manually: PUT /destinations/update-all

    try:
       update_result = update_all_destinations()

       return {
            "message": f"{update_result['updatedCount']} destinations updated successfully",
            "results": update_result["results"],
       }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.put("/{country_code}/update")
def update_destination(country_code: str):
    """
    Updates one destination using live API data.

    Flow:
    1. Get destination from database
    2. Fetch weather, news, and advisory data
    3. Run NLP on news articles
    4. Calculate travel score
    5. Update destination_scores table
    """
 
    try:
        updated_score = update_one_destination(country_code)

        return {
            "message": f"{country_code.upper()} updated successfully",
            "updatedScore": updated_score,
        }

    except ValueError:
        raise HTTPException(status_code=404, detail="Destination not found")

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
    

@router.get("/{country_code}") 
def get_destination(country_code: str): 
    """ 
    Used by DestinationDashboardPage. 
    Returns detailed destination data from PostgreSQL. 
    """ 
    country_code = country_code.upper() 
    conn = get_connection() 
    cur = conn.cursor() 

    try: 
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
        if destination is None: 
            raise HTTPException(status_code=404, detail="Destination not found") 
        return destination
    
    finally:
        cur.close()
        conn.close()