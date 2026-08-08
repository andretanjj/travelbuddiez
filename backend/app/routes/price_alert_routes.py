from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.services.auth_service import User, get_current_active_user
from app.services.price_alert_service import (
    create_flight_price_alert,
    create_hotel_price_alert,
    deactivate_price_alert,
    get_price_alerts_for_user,
)

from app.services.email_service import send_price_alert_email

router = APIRouter(
    prefix="/price-alerts",
    tags=["price alerts"],
)


class CreatePriceAlertRequest(BaseModel):
    """
    Request body used when creating a flight or hotel alert.
    """

    target_price: float = Field(
        ...,
        gt=0,
        description="Price threshold that triggers the alert",
    )

    target_currency: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Currency selected by the user, e.g. SGD",
    )


@router.post("/flights/{saved_flight_id}")
def create_flight_alert(
    saved_flight_id: int,
    request: CreatePriceAlertRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Creates or updates a price alert for one saved flight.
    """

    return create_flight_price_alert(
        username=current_user.username,
        saved_flight_id=saved_flight_id,
        target_price=request.target_price,
        target_currency=request.target_currency,
    )


@router.post("/hotels/{saved_hotel_id}")
def create_hotel_alert(
    saved_hotel_id: int,
    request: CreatePriceAlertRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Creates or updates a price alert for one saved hotel.
    """

    return create_hotel_price_alert(
        username=current_user.username,
        saved_hotel_id=saved_hotel_id,
        target_price=request.target_price,
        target_currency=request.target_currency,
    )


@router.get("")
def get_price_alerts(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Lists all price alerts for the logged-in user.
    """

    return {
        "results": get_price_alerts_for_user(current_user.username),
    }


@router.put("/{alert_id}/deactivate")
def deactivate_alert(
    alert_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Disables one alert while preserving its database history.
    """

    return deactivate_price_alert(
        username=current_user.username,
        alert_id=alert_id,
    )


@router.post("/test-email")
def send_test_price_alert_email(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Temporary development endpoint for verifying Resend integration.

    Remove this endpoint after email delivery is confirmed.
    """

    email_id = send_price_alert_email(
        recipient_email="travelbuddiez.orbital26@gmail.com",
        item_type="flight",
        item_name="Singapore to Tokyo",
        current_price=178.00,
        target_price=300.00,
        currency="USD",
    )

    return {
        "message": "Test email sent",
        "emailId": email_id,
    }