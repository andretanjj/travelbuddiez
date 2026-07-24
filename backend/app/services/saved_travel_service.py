from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.database import get_connection
from app.services.travel_planning_service import search_flights, search_hotels

from app.services.price_alert_service import evaluate_flight_alerts, evaluate_hotel_alerts

from app.services.user_service import get_user_id_by_username


def get_price_status(saved_price: float, current_price: float) -> str:
    """
    Compares saved price against refreshed current price.
    """

    if current_price < saved_price:
        return "price_dropped"

    if current_price > saved_price:
        return "price_increased"

    return "unchanged"


def save_flight_for_user(username: str, flight: dict):
    """
    Saves a flight snapshot for a logged-in user.

    saved_price = price at the time the user clicked Save.
    current_price = latest known price, initially same as saved_price.
    """

    user_id = get_user_id_by_username(username)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO saved_flights (
                user_id,
                origin,
                destination,
                origin_code,
                origin_name,
                destination_code,
                destination_name,
                departure_date,
                return_date,
                price,
                provider,
                airline,
                duration,
                stops,
                currency,
                saved_price,
                current_price,
                saved_at,
                last_checked_at,
                price_status
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s
            )
            RETURNING *;
            """,
            (
                user_id,
                flight.origin_code,
                flight.destination_code,
                flight.origin_code,
                flight.origin_name,
                flight.destination_code,
                flight.destination_name,
                flight.departure_date,
                flight.return_date,
                flight.price,
                flight.provider,
                flight.airline,
                flight.duration,
                flight.stops,
                flight.currency,
                flight.price,
                flight.price,
                "saved_only",
            ),
        )

        saved_flight = cur.fetchone()
        conn.commit()

        return dict(saved_flight)

    except Exception as error:
        conn.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    finally:
        cur.close()
        conn.close()


def save_hotel_for_user(username: str, hotel: dict):
    """
    Saves a hotel snapshot for a logged-in user.

    price is the total stay price from LiteAPI, not per-night price.
    """

    user_id = get_user_id_by_username(username)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO saved_hotels (
                user_id,
                destination_id,
                destination_code,
                destination_name,
                hotel_name,
                city,
                country,
                rating,
                price,
                provider,
                check_in_date,
                check_out_date,
                currency,
                saved_price,
                current_price,
                saved_at,
                last_checked_at,
                price_status
            )
            VALUES (
                %s, NULL, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, NOW(), NOW(), %s
            )
            RETURNING *;
            """,
            (
                user_id,
                hotel.destination_code,
                hotel.destination_name,
                hotel.hotel_name,
                hotel.city,
                hotel.country,
                hotel.rating,
                hotel.price,
                hotel.provider,
                hotel.check_in_date,
                hotel.check_out_date,
                hotel.currency,
                hotel.price,
                hotel.price,
                "saved_only",
            ),
        )

        saved_hotel = cur.fetchone()
        conn.commit()

        return dict(saved_hotel)

    except Exception as error:
        conn.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    finally:
        cur.close()
        conn.close()


def get_saved_flights_for_user(username: str):
    """
    Returns saved flights for the logged-in user.
    """

    user_id = get_user_id_by_username(username)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT *
            FROM saved_flights
            WHERE user_id = %s
            ORDER BY saved_at DESC;
            """,
            (user_id,),
        )

        return [dict(row) for row in cur.fetchall()]

    finally:
        cur.close()
        conn.close()


def get_saved_hotels_for_user(username: str):
    """
    Returns saved hotels for the logged-in user.
    """

    user_id = get_user_id_by_username(username)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT *
            FROM saved_hotels
            WHERE user_id = %s
            ORDER BY saved_at DESC;
            """,
            (user_id,),
        )

        return [dict(row) for row in cur.fetchall()]

    finally:
        cur.close()
        conn.close()


def refresh_saved_flight_price(username: str, saved_flight_id: int):
    """
    Refreshes one saved flight price by running the flight search again.

    For Orbital scope, we compare the saved item against the cheapest current
    matching result for the same route/date.
    """

    user_id = get_user_id_by_username(username)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT *
            FROM saved_flights
            WHERE id = %s AND user_id = %s;
            """,
            (saved_flight_id, user_id),
        )

        saved_flight = cur.fetchone()

        if saved_flight is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved flight not found",
            )

        current_results = search_flights(
            origin=saved_flight["origin_code"] or saved_flight["origin"],
            destination=saved_flight["destination_code"] or saved_flight["destination"],
            departure_date=str(saved_flight["departure_date"]),
            adults=1,
        )

        if len(current_results) == 0:
            new_status = "unavailable"
            current_price = saved_flight["current_price"]
        else:
            cheapest_result = current_results[0]
            current_price = cheapest_result["price"]
            new_status = get_price_status(
                saved_price=float(saved_flight["saved_price"] or saved_flight["price"]),
                current_price=float(current_price),
            )

        cur.execute(
            """
            UPDATE saved_flights
            SET
                current_price = %s,
                last_checked_at = NOW(),
                price_status = %s
            WHERE id = %s AND user_id = %s
            RETURNING *;
            """,
            (
                current_price,
                new_status,
                saved_flight_id,
                user_id,
            ),
        )

        updated_flight = cur.fetchone()

        # Evaluate any active alert linked to this saved flight.
        evaluate_flight_alerts(
            cur=cur,
            saved_flight_id=saved_flight_id,
            current_price=(
                None
                if new_status == "unavailable"
                else float(current_price)
            ),
        )
        conn.commit()

        return dict(updated_flight)

    except HTTPException:
        raise

    except Exception as error:
        conn.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    finally:
        cur.close()
        conn.close()


def refresh_saved_hotel_price(username: str, saved_hotel_id: int):
    """
    Refreshes one saved hotel price by searching hotels again.

    LiteAPI may not return the exact same hotel every time, so for Orbital scope
    we compare against the cheapest current result with the same destination/date.
    """

    user_id = get_user_id_by_username(username)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT *
            FROM saved_hotels
            WHERE id = %s AND user_id = %s;
            """,
            (saved_hotel_id, user_id),
        )

        saved_hotel = cur.fetchone()

        if saved_hotel is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved hotel not found",
            )

        current_results = search_hotels(
            city=saved_hotel["destination_code"],
            check_in_date=str(saved_hotel["check_in_date"]),
            check_out_date=str(saved_hotel["check_out_date"]),
            adults=1,
        )

        if len(current_results) == 0:
            new_status = "unavailable"
            current_price = saved_hotel["current_price"]
        else:
            cheapest_result = current_results[0]
            current_price = cheapest_result["price"]
            new_status = get_price_status(
                saved_price=float(saved_hotel["saved_price"] or saved_hotel["price"]),
                current_price=float(current_price),
            )

        cur.execute(
            """
            UPDATE saved_hotels
            SET
                current_price = %s,
                last_checked_at = NOW(),
                price_status = %s
            WHERE id = %s AND user_id = %s
            RETURNING *;
            """,
            (
                current_price,
                new_status,
                saved_hotel_id,
                user_id,
            ),
        )

        updated_hotel = cur.fetchone()
        
        # Evaluate any active alert linked to this saved hotel.
        evaluate_hotel_alerts(
            cur=cur,
            saved_hotel_id=saved_hotel_id,
            current_price=(
                None
                if new_status == "unavailable"
                else float(current_price)
            ),
        )
        conn.commit()

        return dict(updated_hotel)

    except HTTPException:
        raise

    except Exception as error:
        conn.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    finally:
        cur.close()
        conn.close()


def delete_saved_flight_for_user(
    username: str,
    saved_flight_id: int,
):
    """
    Deletes one saved flight belonging to the logged-in user.

    Any linked price alert is removed automatically because the
    price_alerts foreign key uses ON DELETE CASCADE.
    """

    user_id = get_user_id_by_username(username)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            DELETE FROM saved_flights
            WHERE id = %s
              AND user_id = %s
            RETURNING id;
            """,
            (
                saved_flight_id,
                user_id,
            ),
        )

        deleted_flight = cur.fetchone()

        if deleted_flight is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved flight not found",
            )

        conn.commit()

        return {
            "message": "Saved flight deleted successfully",
            "deletedId": deleted_flight["id"],
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as error:
        conn.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    finally:
        cur.close()
        conn.close()


def delete_saved_hotel_for_user(
    username: str,
    saved_hotel_id: int,
):
    """
    Deletes one saved hotel belonging to the logged-in user.

    Any linked price alert is removed automatically because the
    price_alerts foreign key uses ON DELETE CASCADE.
    """

    user_id = get_user_id_by_username(username)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            DELETE FROM saved_hotels
            WHERE id = %s
              AND user_id = %s
            RETURNING id;
            """,
            (
                saved_hotel_id,
                user_id,
            ),
        )

        deleted_hotel = cur.fetchone()

        if deleted_hotel is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved hotel not found",
            )

        conn.commit()

        return {
            "message": "Saved hotel deleted successfully",
            "deletedId": deleted_hotel["id"],
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as error:
        conn.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    finally:
        cur.close()
        conn.close()