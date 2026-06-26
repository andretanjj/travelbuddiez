# this lazy refresh approach is used to update the data for MapView
# data is only updated (using RSS feed) if data is older than 12 hours
# backend checks updated time when GET /destinations is called

from datetime import datetime, timedelta, timezone
from app.database import get_connection
from app.services.update_map_scores_service import update_map_scores

def check_last_updated_map_scores(hours: int = 12) -> bool:
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT MAX(last_updated) AS latest_updated
            FROM destination_map_scores;
        """)
        # checks the most recent last_updated value in the table (most recent country)
        # this saves time as it only checks one country instead of all countries

        row = cur.fetchone()

        if row is None: 
            update_map_scores()
            return True

        latest_updated = row["latest_updated"] # latest update time

        if latest_updated is None: 
            update_map_scores()
            return True

        now = datetime.now(timezone.utc)

        if latest_updated.tzinfo is None:
            latest_updated = latest_updated.replace(tzinfo=timezone.utc) # to avoid timezone errors

        outdated =  now - latest_updated >= timedelta(hours=hours)

        if outdated:
            update_map_scores()
            return True

        return False

    finally:
        cur.close()
        conn.close()