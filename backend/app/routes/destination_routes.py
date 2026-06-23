from fastapi import APIRouter, HTTPException

from app.database import get_connection
from app.services.update_dest_scores_service import (
    update_all_destinations,
    update_one_destination
)
from app.services.update_map_advisory_service import update_map_advisories

router = APIRouter(
    prefix="/destinations",
    tags=["destinations"],
)

@router.put("/map-advisories/update-all")
def update_all_map_advisories():
    # this is for manual update of map advisory data from rss feed

    try:
        updated_count = update_map_advisories()

        return {
            "message": f"{updated_count} map advisories updated successfully"
        }
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.get("")
def get_all_destinations():
    """
    Used by MapView
    Returns mapScore for map coloring and tooltip.
    Does NOT call weather/news APIs.
    returns data frm database
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            d.country_code AS "countryCode",
            d.country_name AS country,
            d.city,
            ma.map_score AS "mapScore",
            ma.risk_level AS "riskLevel",
            ma.condition_summary AS condition,
            ma.last_updated AS "lastUpdated"
        FROM destinations d
        LEFT JOIN map_advisories ma
        ON d.id = ma.destination_id
        ORDER BY d.country_name;
    """)

    all_destinations = cur.fetchall()

    cur.close()
    conn.close()

    return all_destinations


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


@router.get("/{country_code}") 
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

@router.put("/{country_code}/update")
def update_destination(country_code: str):
    """
    Updates one destination using live API data.

    Flow:
    1. Get destination from database
    2. Fetch weather, news, and advisory data
    3. Calculate travel score
    4. Update destination_scores table
    5. Return updated destination data
    """
 
    try:
        updated_score = update_one_destination(country_code)

        return {
            "message": f"{country_code} updated successfully",
            "updatedScore": updated_score,
        }

    except ValueError:
        raise HTTPException(status_code=404, detail="Destination not found")

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))