"""
Seed airports from OurAirports airports.csv into travel_places.

Run from the backend folder:

    python3 -m app.scripts.seed_airports

Expected CSV location:

    backend/app/data/airports.csv

What this script does:
1. Reads airports.csv
2. Filters usable airports
3. Inserts airports into travel_places in batches
4. Skips duplicates
"""

import csv
from pathlib import Path

from dotenv import load_dotenv
from psycopg2.extras import execute_values

from app.database import get_connection


# Load backend .env so DATABASE_URL is available when running this script locally.
load_dotenv()


# This file is at:
# backend/app/scripts/seed_airports.py
#
# Path(__file__).resolve().parent        = backend/app/scripts
# Path(__file__).resolve().parent.parent = backend/app
APP_DIR = Path(__file__).resolve().parent.parent
AIRPORTS_CSV_PATH = APP_DIR / "data" / "airports.csv"


# Insert this many airports per database query.
# 500 is a safe size for Supabase/PostgreSQL.
BATCH_SIZE = 500


def clean_text(value):
    """
    Converts empty strings into None and trims whitespace.
    """

    if value is None:
        return None

    cleaned_value = value.strip()

    if cleaned_value == "":
        return None

    return cleaned_value


def clean_float(value):
    """
    Safely converts latitude/longitude strings into floats.
    """

    cleaned_value = clean_text(value)

    if cleaned_value is None:
        return None

    try:
        return float(cleaned_value)
    except ValueError:
        return None


def is_usable_airport(row):
    """
    Filters OurAirports rows for TravelBuddiez autocomplete.

    We only keep airports that:
    - are not closed
    - have an IATA code, e.g. SIN, HND, FRA
    - are useful airport types, not heliports or seaplane bases
    """

    airport_type = clean_text(row.get("type"))
    iata_code = clean_text(row.get("iata_code"))
    airport_name = clean_text(row.get("name"))

    allowed_airport_types = {
        "large_airport",
        "medium_airport",
        "small_airport",
    }

    if airport_type not in allowed_airport_types:
        return False

    if iata_code is None:
        return False

    if airport_name is None:
        return False

    return True


def get_priority(row):
    """
    Lower priority appears earlier in autocomplete.

    Large airports should appear before smaller airports.
    Airports with scheduled service should also rank higher.
    """

    airport_type = clean_text(row.get("type"))
    scheduled_service = clean_text(row.get("scheduled_service"))

    if airport_type == "large_airport":
        return 2

    if airport_type == "medium_airport" and scheduled_service == "yes":
        return 3

    if airport_type == "medium_airport":
        return 4

    return 6


def build_search_keywords(row):
    """
    Builds searchable text for ILIKE matching.

    Example:
    "frankfurt frankfurt airport fra eddf de"
    """

    values = [
        row.get("name"),
        row.get("municipality"),
        row.get("iata_code"),
        row.get("ident"),
        row.get("iso_country"),
        row.get("keywords"),
    ]

    cleaned_values = []

    for value in values:
        cleaned_value = clean_text(value)

        if cleaned_value is not None:
            cleaned_values.append(cleaned_value.lower())

    return " ".join(cleaned_values)


def normalise_airport_row(row):
    """
    Converts one OurAirports CSV row into a tuple for batch insert.

    The tuple order must match the INSERT column order in insert_airport_batch().
    """

    airport_id = clean_text(row.get("id"))
    ident = clean_text(row.get("ident"))
    airport_name = clean_text(row.get("name"))
    iata_code = clean_text(row.get("iata_code"))
    municipality = clean_text(row.get("municipality"))
    iso_country = clean_text(row.get("iso_country"))

    latitude = clean_float(row.get("latitude_deg"))
    longitude = clean_float(row.get("longitude_deg"))

    # Use municipality as city when available.
    # If missing, fallback to airport name.
    city = municipality or airport_name

    # OurAirports airports.csv mainly gives iso_country.
    # If your CSV has country_name, use it. Otherwise use iso_country.
    country = clean_text(row.get("country_name")) or iso_country

    # Stable source id for duplicate prevention.
    source_id = airport_id or ident or iata_code

    subtitle = f"{city}, {country}" if city and country else country

    return (
        airport_name,
        subtitle,
        iata_code,
        city,
        country,
        iso_country,
        "airport",
        build_search_keywords(row),
        get_priority(row),
        "ourairports",
        source_id,
        latitude,
        longitude,
    )


def insert_airport_batch(cur, airport_batch):
    """
    Inserts many airports at once.

    execute_values is much faster than calling cur.execute once per airport.

    ON CONFLICT DO NOTHING skips duplicates from:
    - UNIQUE(name, subtitle, place_type)
    - unique provider/source_id index
    """

    if len(airport_batch) == 0:
        return

    execute_values(
        cur,
        """
        INSERT INTO travel_places (
            name,
            subtitle,
            code,
            city,
            country,
            country_code,
            place_type,
            search_keywords,
            priority,
            provider,
            source_id,
            latitude,
            longitude
        )
        VALUES %s
        ON CONFLICT DO NOTHING;
        """,
        airport_batch,
    )


def seed_airports():
    """
    Main script runner.
    """

    if not AIRPORTS_CSV_PATH.exists():
        raise FileNotFoundError(f"Cannot find airports.csv at {AIRPORTS_CSV_PATH}")

    conn = get_connection()
    cur = conn.cursor()

    total_rows = 0
    usable_rows = 0
    batch = []

    try:
        print(f"Reading airport data from: {AIRPORTS_CSV_PATH}")

        with AIRPORTS_CSV_PATH.open("r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)

            for row in reader:
                total_rows += 1

                if not is_usable_airport(row):
                    continue

                usable_rows += 1

                airport_tuple = normalise_airport_row(row)
                batch.append(airport_tuple)

                # Insert and commit every BATCH_SIZE airports.
                if len(batch) >= BATCH_SIZE:
                    insert_airport_batch(cur, batch)
                    conn.commit()

                    print(f"Processed and committed {usable_rows} usable airports...")

                    batch = []

            # Insert remaining airports after loop ends.
            if len(batch) > 0:
                insert_airport_batch(cur, batch)
                conn.commit()

                print(f"Processed and committed {usable_rows} usable airports...")

        print("Airport seed completed.")
        print(f"Total CSV rows read: {total_rows}")
        print(f"Usable airport rows: {usable_rows}")
        print("Duplicates were skipped using ON CONFLICT DO NOTHING.")

    except Exception:
        conn.rollback()
        raise

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    seed_airports()