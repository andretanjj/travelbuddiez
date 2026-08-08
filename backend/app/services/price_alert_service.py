from fastapi import HTTPException, status

from app.database import get_connection
from app.services.user_service import get_user_id_by_username

from app.services.email_service import send_price_alert_email

from app.services.currency_service import (
    SUPPORTED_CURRENCIES,
    convert_currency_amount,
)


def create_flight_price_alert(
    username: str,
    saved_flight_id: int,
    target_price: float,
    target_currency: str,
):
    """
    Creates or updates a flight price alert.

    The user chooses the alert currency.
    Provider prices are converted into that currency before comparison.

    When the latest known flight price is already at or below the target,
    the notification email is sent immediately.
    """

    if target_price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target price must be greater than zero",
        )

    target_currency = target_currency.upper()

    if target_currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported alert currency: {target_currency}",
        )

    user_id = get_user_id_by_username(username)

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Verify ownership and retrieve the information needed
        # for comparison and email delivery.
        cur.execute(
            """
            SELECT
                sf.id,
                sf.current_price,
                sf.currency,
                sf.origin_name,
                sf.destination_name,
                sf.departure_date,
                sf.return_date,
                u.email
            FROM saved_flights AS sf
            JOIN users AS u
                ON u.id = sf.user_id
            WHERE sf.id = %s
              AND sf.user_id = %s;
            """,
            (
                saved_flight_id,
                user_id,
            ),
        )

        saved_flight = cur.fetchone()

        if saved_flight is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved flight not found",
            )

        current_price = saved_flight["current_price"]

        target_reached = False
        converted_current_price = None

        if current_price is not None:
            try:
                # Convert the provider price into the currency
                # chosen by the user for this alert.
                converted_current_price = convert_currency_amount(
                    amount=float(current_price),
                    from_currency=saved_flight["currency"],
                    to_currency=target_currency,
                )

                target_reached = (
                    converted_current_price <= float(target_price)
                )

            except (ValueError, RuntimeError) as error:
                # Saving the alert should still succeed if the FX service
                # is temporarily unavailable.
                print(
                    f"Unable to convert flight price for alert: {error}"
                )

        initial_status = "triggered" if target_reached else "pending"

        # Check for an existing alert, including an inactive alert.
        cur.execute(
            """
            SELECT id
            FROM price_alerts
            WHERE user_id = %s
              AND alert_type = 'flight'
              AND saved_flight_id = %s
            ORDER BY created_at DESC
            LIMIT 1;
            """,
            (
                user_id,
                saved_flight_id,
            ),
        )

        existing_alert = cur.fetchone()

        if existing_alert is not None:
            cur.execute(
                """
                UPDATE price_alerts
                SET
                    target_price = %s,
                    target_currency = %s,
                    is_active = TRUE,
                    notification_status = %s,
                    last_checked_at = NOW(),
                    last_notified_at = NULL,
                    updated_at = NOW()
                WHERE id = %s
                  AND user_id = %s
                RETURNING *;
                """,
                (
                    target_price,
                    target_currency,
                    initial_status,
                    existing_alert["id"],
                    user_id,
                ),
            )

            saved_alert = cur.fetchone()

        else:
            cur.execute(
                """
                INSERT INTO price_alerts (
                    user_id,
                    alert_type,
                    target_price,
                    target_currency,
                    is_active,
                    saved_flight_id,
                    saved_hotel_id,
                    notification_status,
                    last_checked_at,
                    last_notified_at,
                    created_at,
                    updated_at
                )
                VALUES (
                    %s,
                    'flight',
                    %s,
                    %s,
                    TRUE,
                    %s,
                    NULL,
                    %s,
                    NOW(),
                    NULL,
                    NOW(),
                    NOW()
                )
                RETURNING *;
                """,
                (
                    user_id,
                    target_price,
                    target_currency,
                    saved_flight_id,
                    initial_status,
                ),
            )

            saved_alert = cur.fetchone()

        # Send immediately when the converted current price
        # already meets the user's target.
        if (
            target_reached
            and converted_current_price is not None
        ):
            item_name = (
                f'{saved_flight["origin_name"]} to '
                f'{saved_flight["destination_name"]}'
            )

            try:
                send_price_alert_email(
                    recipient_email=saved_flight["email"],
                    item_type="flight",
                    item_name=item_name,
                    current_price=converted_current_price,
                    target_price=float(target_price),
                    currency=target_currency,
                    trip_type=(
                        "Round trip"
                        if saved_flight["return_date"]
                        else "One way"
                    ),
                    departure_date=str(saved_flight["departure_date"]),
                    return_date=(
                        str(saved_flight["return_date"])
                        if saved_flight["return_date"]
                        else None
                    ),
                )

                cur.execute(
                    """
                    UPDATE price_alerts
                    SET
                        notification_status = 'notified',
                        last_notified_at = NOW(),
                        updated_at = NOW()
                    WHERE id = %s
                    RETURNING *;
                    """,
                    (saved_alert["id"],),
                )

                saved_alert = cur.fetchone()

            except Exception as error:
                # Keep the alert as triggered so Celery can retry it later.
                print(
                    f"Unable to send flight alert email "
                    f"for alert {saved_alert['id']}: {error}"
                )

        conn.commit()

        return dict(saved_alert)

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
    target_currency: str,
):
    """
    Creates or updates a hotel price alert.

    The user chooses the alert currency.
    Provider prices are converted into that currency before comparison.

    When the latest known hotel price is already at or below the target,
    the notification email is sent immediately.
    """

    if target_price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target price must be greater than zero",
        )

    target_currency = target_currency.upper()

    if target_currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported alert currency: {target_currency}",
        )

    user_id = get_user_id_by_username(username)

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Verify ownership and retrieve the information needed
        # for comparison and email delivery.
        cur.execute(
            """
            SELECT
                sh.id,
                sh.current_price,
                sh.currency,
                sh.hotel_name,
                sh.city,
                sh.country,
                u.email
            FROM saved_hotels AS sh
            JOIN users AS u
                ON u.id = sh.user_id
            WHERE sh.id = %s
              AND sh.user_id = %s;
            """,
            (
                saved_hotel_id,
                user_id,
            ),
        )

        saved_hotel = cur.fetchone()

        if saved_hotel is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved hotel not found",
            )

        current_price = saved_hotel["current_price"]

        target_reached = False
        converted_current_price = None

        if current_price is not None:
            try:
                # Convert the provider price into the currency
                # selected by the user.
                converted_current_price = convert_currency_amount(
                    amount=float(current_price),
                    from_currency=saved_hotel["currency"],
                    to_currency=target_currency,
                )

                target_reached = (
                    converted_current_price <= float(target_price)
                )

            except (ValueError, RuntimeError) as error:
                print(
                    f"Unable to convert hotel price for alert: {error}"
                )

        initial_status = "triggered" if target_reached else "pending"

        cur.execute(
            """
            SELECT id
            FROM price_alerts
            WHERE user_id = %s
              AND alert_type = 'hotel'
              AND saved_hotel_id = %s
            ORDER BY created_at DESC
            LIMIT 1;
            """,
            (
                user_id,
                saved_hotel_id,
            ),
        )

        existing_alert = cur.fetchone()

        if existing_alert is not None:
            cur.execute(
                """
                UPDATE price_alerts
                SET
                    target_price = %s,
                    target_currency = %s,
                    is_active = TRUE,
                    notification_status = %s,
                    last_checked_at = NOW(),
                    last_notified_at = NULL,
                    updated_at = NOW()
                WHERE id = %s
                  AND user_id = %s
                RETURNING *;
                """,
                (
                    target_price,
                    target_currency,
                    initial_status,
                    existing_alert["id"],
                    user_id,
                ),
            )

            saved_alert = cur.fetchone()

        else:
            cur.execute(
                """
                INSERT INTO price_alerts (
                    user_id,
                    alert_type,
                    target_price,
                    target_currency,
                    is_active,
                    saved_flight_id,
                    saved_hotel_id,
                    notification_status,
                    last_checked_at,
                    last_notified_at,
                    created_at,
                    updated_at
                )
                VALUES (
                    %s,
                    'hotel',
                    %s,
                    %s,
                    TRUE,
                    NULL,
                    %s,
                    %s,
                    NOW(),
                    NULL,
                    NOW(),
                    NOW()
                )
                RETURNING *;
                """,
                (
                    user_id,
                    target_price,
                    target_currency,
                    saved_hotel_id,
                    initial_status,
                ),
            )

            saved_alert = cur.fetchone()

        if (
            target_reached
            and converted_current_price is not None
        ):
            item_name = (
                f'{saved_hotel["hotel_name"]}, '
                f'{saved_hotel["city"]}, '
                f'{saved_hotel["country"]}'
            )

            try:
                send_price_alert_email(
                    recipient_email=saved_hotel["email"],
                    item_type="hotel",
                    item_name=item_name,
                    current_price=converted_current_price,
                    target_price=float(target_price),
                    currency=target_currency,
                )

                cur.execute(
                    """
                    UPDATE price_alerts
                    SET
                        notification_status = 'notified',
                        last_notified_at = NOW(),
                        updated_at = NOW()
                    WHERE id = %s
                    RETURNING *;
                    """,
                    (saved_alert["id"],),
                )

                saved_alert = cur.fetchone()

            except Exception as error:
                # Remains triggered so the scheduled checker can retry later.
                print(
                    f"Unable to send hotel alert email "
                    f"for alert {saved_alert['id']}: {error}"
                )

        conn.commit()

        return dict(saved_alert)

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


def evaluate_flight_alerts(
    cur,
    saved_flight_id: int,
    current_price: float | None,
):
    """
    Evaluates active alerts linked to one saved flight.

    The provider price is converted into each alert's target currency
    before comparison.

    Status flow:
    - unavailable: no current price was returned
    - pending: converted current price is above the user's target
    - notified: target was reached and the email was sent
    - triggered: target was reached, but email delivery failed

    Alerts already marked as notified are not emailed repeatedly.
    """

    cur.execute(
        """
        SELECT
            pa.id,
            pa.target_price,
            pa.target_currency,
            pa.notification_status,
            pa.last_notified_at,
            u.email,
            sf.origin_name,
            sf.destination_name,
            sf.currency,
            sf.departure_date,
            sf.return_date,
        FROM price_alerts AS pa
        JOIN users AS u
            ON u.id = pa.user_id
        JOIN saved_flights AS sf
            ON sf.id = pa.saved_flight_id
        WHERE pa.alert_type = 'flight'
          AND pa.saved_flight_id = %s
          AND pa.is_active = TRUE;
        """,
        (saved_flight_id,),
    )

    alerts = cur.fetchall()

    for alert in alerts:
        # No current result was returned by Duffel.
        if current_price is None:
            cur.execute(
                """
                UPDATE price_alerts
                SET
                    notification_status = 'unavailable',
                    last_checked_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (alert["id"],),
            )

            continue

        target_price = float(alert["target_price"])
        provider_price = float(current_price)

        try:
            # Always use the latest available exchange rate
            # when evaluating the alert.
            latest_price = convert_currency_amount(
                amount=provider_price,
                from_currency=alert["currency"],
                to_currency=alert["target_currency"],
            )

        except (ValueError, RuntimeError) as error:
            # Do not compare currencies when conversion failed.
            print(
                f"Unable to convert flight price "
                f"for alert {alert['id']}: {error}"
            )

            cur.execute(
                """
                UPDATE price_alerts
                SET
                    last_checked_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (alert["id"],),
            )

            continue

        # Converted price is still above the user's target.
        if latest_price > target_price:
            cur.execute(
                """
                UPDATE price_alerts
                SET
                    notification_status = 'pending',
                    last_checked_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (alert["id"],),
            )

            continue

        # Do not send the same alert repeatedly after a successful email.
        if (
            alert["notification_status"] == "notified"
            and alert["last_notified_at"] is not None
        ):
            cur.execute(
                """
                UPDATE price_alerts
                SET
                    last_checked_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (alert["id"],),
            )

            continue

        item_name = (
            f'{alert["origin_name"]} to '
            f'{alert["destination_name"]}'
        )

        try:
            send_price_alert_email(
                recipient_email=alert["email"],
                item_type="flight",
                item_name=item_name,
                current_price=latest_price,
                target_price=target_price,
                currency=alert["target_currency"],
                trip_type=(
                    "Round trip"
                    if alert["return_date"]
                    else "One way"
                ),
                departure_date=str(alert["departure_date"]),
                return_date=(
                    str(alert["return_date"])
                    if alert["return_date"]
                    else None
                ),
            )

            # Email was successfully accepted by Resend.
            cur.execute(
                """
                UPDATE price_alerts
                SET
                    notification_status = 'notified',
                    last_checked_at = NOW(),
                    last_notified_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (alert["id"],),
            )

        except Exception as error:
            # Keep the price refresh successful even when email delivery fails.
            # The triggered state allows a later scheduled check to retry.
            print(
                f"Unable to send flight alert email "
                f"for alert {alert['id']}: {error}"
            )

            cur.execute(
                """
                UPDATE price_alerts
                SET
                    notification_status = 'triggered',
                    last_checked_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (alert["id"],),
            )


def evaluate_hotel_alerts(
    cur,
    saved_hotel_id: int,
    current_price: float | None,
):
    """
    Evaluates active alerts linked to one saved hotel.

    The provider price is converted into each alert's target currency
    before comparison and email delivery.
    """

    cur.execute(
        """
        SELECT
            pa.id,
            pa.target_price,
            pa.target_currency,
            pa.notification_status,
            pa.last_notified_at,
            u.email,
            sh.hotel_name,
            sh.city,
            sh.country,
            sh.currency
        FROM price_alerts AS pa
        JOIN users AS u
            ON u.id = pa.user_id
        JOIN saved_hotels AS sh
            ON sh.id = pa.saved_hotel_id
        WHERE pa.alert_type = 'hotel'
          AND pa.saved_hotel_id = %s
          AND pa.is_active = TRUE;
        """,
        (saved_hotel_id,),
    )

    alerts = cur.fetchall()

    for alert in alerts:
        if current_price is None:
            cur.execute(
                """
                UPDATE price_alerts
                SET
                    notification_status = 'unavailable',
                    last_checked_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (alert["id"],),
            )

            continue

        target_price = float(alert["target_price"])
        provider_price = float(current_price)

        try:
            # Always compare using the user's selected alert currency.
            latest_price = convert_currency_amount(
                amount=provider_price,
                from_currency=alert["currency"],
                to_currency=alert["target_currency"],
            )

        except (ValueError, RuntimeError) as error:
            print(
                f"Unable to convert hotel price "
                f"for alert {alert['id']}: {error}"
            )

            cur.execute(
                """
                UPDATE price_alerts
                SET
                    last_checked_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (alert["id"],),
            )

            continue

        # Converted price is still above the user's target.
        if latest_price > target_price:
            cur.execute(
                """
                UPDATE price_alerts
                SET
                    notification_status = 'pending',
                    last_checked_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (alert["id"],),
            )

            continue

        if (
            alert["notification_status"] == "notified"
            and alert["last_notified_at"] is not None
        ):
            cur.execute(
                """
                UPDATE price_alerts
                SET
                    last_checked_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (alert["id"],),
            )

            continue

        item_name = (
            f'{alert["hotel_name"]}, '
            f'{alert["city"]}, '
            f'{alert["country"]}'
        )

        try:
            send_price_alert_email(
                recipient_email=alert["email"],
                item_type="hotel",
                item_name=item_name,
                current_price=latest_price,
                target_price=target_price,
                currency=alert["target_currency"],
            )

            cur.execute(
                """
                UPDATE price_alerts
                SET
                    notification_status = 'notified',
                    last_checked_at = NOW(),
                    last_notified_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (alert["id"],),
            )

        except Exception as error:
            print(
                f"Unable to send hotel alert email "
                f"for alert {alert['id']}: {error}"
            )

            cur.execute(
                """
                UPDATE price_alerts
                SET
                    notification_status = 'triggered',
                    last_checked_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s;
                """,
                (alert["id"],),
            )