import os

import resend
from dotenv import load_dotenv


load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.getenv(
    "RESEND_FROM_EMAIL",
    "TravelBuddiez <onboarding@resend.dev>",
)

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


def send_price_alert_email(
    recipient_email: str,
    item_type: str,
    item_name: str,
    current_price: float,
    target_price: float,
    currency: str,
    trip_type: str | None = None,
    departure_date: str | None = None,
    return_date: str | None = None,
) -> str:
    """
    Sends a price-alert email through Resend.

    Returns the Resend email ID when successful.
    """

    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY is not configured.")

    cleaned_item_type = item_type.strip().lower()

    if cleaned_item_type not in {"flight", "hotel"}:
        raise ValueError("item_type must be either 'flight' or 'hotel'.")

    subject = (
        f"TravelBuddiez {cleaned_item_type} price alert: "
        f"{item_name}"
    )

    trip_details_html = ""

    if cleaned_item_type == "flight":
        trip_details_html = f"""
            <p>
                <strong>Trip type:</strong>
                {trip_type or "One way"}
            </p>
        """

        if departure_date:
            if return_date:
                trip_details_html += f"""
                    <p>
                        <strong>Outbound:</strong> {departure_date}<br>
                        <strong>Return:</strong> {return_date}
                    </p>
                """
            else:
                trip_details_html += f"""
                    <p>
                        <strong>Departure:</strong> {departure_date}
                    </p>
                """

    html = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h2>Your {cleaned_item_type} price target has been reached</h2>

        <p>
            The latest price for <strong>{item_name}</strong>
            is now within your target.
        </p>

        {trip_details_html}

        <p>
            <strong>Current price:</strong>
            {currency} {current_price:.2f}
        </p>

        <p>
            <strong>Your target:</strong>
            {currency} {target_price:.2f}
        </p>

        <p>
            Prices and availability may change. Open TravelBuddiez
            and refresh the saved item before booking.
        </p>
    </div>
    """

    params: resend.Emails.SendParams = {
        "from": RESEND_FROM_EMAIL,
        "to": [recipient_email],
        "subject": subject,
        "html": html,
    }

    response = resend.Emails.send(params)

    email_id = response.get("id")

    if not email_id:
        raise RuntimeError("Resend did not return an email ID.")

    return email_id