from fastapi import HTTPException, status

from app.database import get_connection
from app.services.saved_travel_service import get_user_id_by_username


def create_flight_price_alert(
    username: str,
    saved_flight_id: int,
    target_price: float,
):
    """
    Creates or updates an active price alert for one saved flight.

    The saved flight must belong to the logged-in user.
    """

    user_id = get_user_id_by_username(username)

    if target_price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target price must be greater than zero",
        )

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Confirm that the saved flight belongs to the current user.
        cur.execute(
            """
            SELECT id
            FROM saved_flights
            WHERE id = %s
              AND user_id = %s;
            """,
            (saved_flight_id, user_id),
        )

        if cur.fetchone() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved flight not found",
            )

        # Reuse an existing active alert instead of creating duplicates.
        cur.execute(
            """
            SELECT id
            FROM price_alerts
            WHERE user_id = %s
              AND alert_type = 'flight'
              AND saved_flight_id = %s
              AND is_active = TRUE;
            """,
            (user_id, saved_flight_id),
        )

        existing_alert = cur.fetchone()

        if existing_alert:
            cur.execute(
                """
                UPDATE price_alerts
                SET
                    target_price = %s,
                    notification_status = 'pending',
                    updated_at = NOW()
                WHERE id = %s
                RETURNING *;
                """,
                (
                    target_price,
                    existing_alert["id"],
                ),
            )
        else:
            cur.execute(
                """
                INSERT INTO price_alerts (
                    user_id,
                    alert_type,
                    target_price,
                    is_active,
                    saved_flight_id,
                    saved_hotel_id,
                    notification_status,
                    created_at,
                    updated_at
                )
                VALUES (
                    %s,
                    'flight',
                    %s,
                    TRUE,
                    %s,
                    NULL,
                    'pending',
                    NOW(),
                    NOW()
                )
                RETURNING *;
                """,
                (
                    user_id,
                    target_price,
                    saved_flight_id,
                ),
            )

        alert = cur.fetchone()
        conn.commit()

        return dict(alert)

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


def create_hotel_price_alert(
    username: str,
    saved_hotel_id: int,
    target_price: float,
):
    """
    Creates or updates an active price alert for one saved hotel.

    The saved hotel must belong to the logged-in user.
    """

    user_id = get_user_id_by_username(username)

    if target_price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target price must be greater than zero",
        )

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Confirm that the saved hotel belongs to the current user.
        cur.execute(
            """
            SELECT id
            FROM saved_hotels
            WHERE id = %s
              AND user_id = %s;
            """,
            (saved_hotel_id, user_id),
        )

        if cur.fetchone() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved hotel not found",
            )

        # Reuse an existing active alert instead of creating duplicates.
        cur.execute(
            """
            SELECT id
            FROM price_alerts
            WHERE user_id = %s
              AND alert_type = 'hotel'
              AND saved_hotel_id = %s
              AND is_active = TRUE;
            """,
            (user_id, saved_hotel_id),
        )

        existing_alert = cur.fetchone()

        if existing_alert:
            cur.execute(
                """
                UPDATE price_alerts
                SET
                    target_price = %s,
                    notification_status = 'pending',
                    updated_at = NOW()
                WHERE id = %s
                RETURNING *;
                """,
                (
                    target_price,
                    existing_alert["id"],
                ),
            )
        else:
            cur.execute(
                """
                INSERT INTO price_alerts (
                    user_id,
                    alert_type,
                    target_price,
                    is_active,
                    saved_flight_id,
                    saved_hotel_id,
                    notification_status,
                    created_at,
                    updated_at
                )
                VALUES (
                    %s,
                    'hotel',
                    %s,
                    TRUE,
                    NULL,
                    %s,
                    'pending',
                    NOW(),
                    NOW()
                )
                RETURNING *;
                """,
                (
                    user_id,
                    target_price,
                    saved_hotel_id,
                ),
            )

        alert = cur.fetchone()
        conn.commit()

        return dict(alert)

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


def get_price_alerts_for_user(username: str):
    """
    Returns all price alerts belonging to the logged-in user.
    """

    user_id = get_user_id_by_username(username)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                pa.*,
                sf.origin_name AS flight_origin_name,
                sf.destination_name AS flight_destination_name,
                sf.current_price AS flight_current_price,
                sh.hotel_name,
                sh.destination_name AS hotel_destination_name,
                sh.current_price AS hotel_current_price
            FROM price_alerts pa
            LEFT JOIN saved_flights sf
                ON pa.saved_flight_id = sf.id
            LEFT JOIN saved_hotels sh
                ON pa.saved_hotel_id = sh.id
            WHERE pa.user_id = %s
            ORDER BY pa.created_at DESC;
            """,
            (user_id,),
        )

        return [dict(row) for row in cur.fetchall()]

    finally:
        cur.close()
        conn.close()


def deactivate_price_alert(username: str, alert_id: int):
    """
    Deactivates an alert without deleting its history.
    """

    user_id = get_user_id_by_username(username)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE price_alerts
            SET
                is_active = FALSE,
                updated_at = NOW()
            WHERE id = %s
              AND user_id = %s
            RETURNING *;
            """,
            (
                alert_id,
                user_id,
            ),
        )

        alert = cur.fetchone()

        if alert is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Price alert not found",
            )

        conn.commit()

        return dict(alert)

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