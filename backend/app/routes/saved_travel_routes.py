from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.services.auth_service import User, get_current_active_user
from app.services.saved_travel_service import (
    delete_saved_flight_for_user,
    delete_saved_hotel_for_user,
    get_saved_flights_for_user,
    get_saved_hotels_for_user,
    refresh_saved_flight_price,
    refresh_saved_hotel_price,
    save_flight_for_user,
    save_hotel_for_user,
)


router = APIRouter(
    prefix="/saved-travel",
    tags=["saved travel"],
)


class SaveFlightRequest(BaseModel):
    provider_item_id: str
    origin_code: str
    origin_name: str
    destination_code: str
    destination_name: str
    departure_date: str
    return_date: str | None = None
    price: float
    currency: str
    airline: str
    flight_number: str | None = None
    departure_at: str | None = None
    duration: str
    stops: str
    provider: str = "duffel"


class SaveHotelRequest(BaseModel):
    provider_item_id: str
    destination_code: str
    destination_name: str
    hotel_name: str
    city: str
    country: str
    rating: float
    price: float
    currency: str
    check_in_date: str
    check_out_date: str
    provider: str = "liteapi"


@router.post("/flights")
def save_flight(
    request: SaveFlightRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Saves a flight snapshot for the logged-in user.

    Requires Authorization: Bearer <token>.
    """

    return save_flight_for_user(
        username=current_user.username,
        flight=request,
    )


@router.post("/hotels")
def save_hotel(
    request: SaveHotelRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Saves a hotel snapshot for the logged-in user.

    Requires Authorization: Bearer <token>.
    """

    return save_hotel_for_user(
        username=current_user.username,
        hotel=request,
    )


@router.get("/flights")
def get_saved_flights(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Lists saved flights for the logged-in user.
    """

    return {
        "results": get_saved_flights_for_user(current_user.username),
    }


@router.get("/hotels")
def get_saved_hotels(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Lists saved hotels for the logged-in user.
    """

    return {
        "results": get_saved_hotels_for_user(current_user.username),
    }


@router.put("/flights/{saved_flight_id}/refresh")
def refresh_flight_price(
    saved_flight_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Refreshes the latest known price for one saved flight.
    """

    return refresh_saved_flight_price(
        username=current_user.username,
        saved_flight_id=saved_flight_id,
    )


@router.put("/hotels/{saved_hotel_id}/refresh")
def refresh_hotel_price(
    saved_hotel_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Refreshes the latest known price for one saved hotel.
    """

    return refresh_saved_hotel_price(
        username=current_user.username,
        saved_hotel_id=saved_hotel_id,
    )


@router.delete("/flights/{saved_flight_id}")
def delete_saved_flight(
    saved_flight_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Deletes one saved flight belonging to the logged-in user.
    """

    return delete_saved_flight_for_user(
        username=current_user.username,
        saved_flight_id=saved_flight_id,
    )


@router.delete("/hotels/{saved_hotel_id}")
def delete_saved_hotel(
    saved_hotel_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Deletes one saved hotel belonging to the logged-in user.
    """

    return delete_saved_hotel_for_user(
        username=current_user.username,
        saved_hotel_id=saved_hotel_id,
    )