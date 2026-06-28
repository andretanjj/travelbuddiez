from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.services.auth_service import (
    ACCESS_TOKEN_EXPIRY_MINUTES,
    Token,
    User,
    authenticate_user,
    create_access_token,
    create_user,
    get_current_active_user,
)


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


class RegisterRequest(BaseModel):
    # Username is displayed in the app.
    username: str

    # Email can be used for login.
    email: str

    # Plain password is received here, then hashed in auth_service.py.
    password: str


@router.post("/register", response_model=User)
def register_user(request: RegisterRequest):
    """
    Registers a new TravelBuddiez user.
    Login + Account Creation.
    """
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )

    return create_user(
        username=request.username,
        email=request.email,
        password=request.password,
    )


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """
    Logs in the user and returns a JWT bearer token.
    The frontend sends the user's email or username as the form field "username".
    """
    user = authenticate_user(
        username_or_email=form_data.username,
        password=form_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(
        minutes=ACCESS_TOKEN_EXPIRY_MINUTES,
    )

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
    )


@router.get("/me", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """
    Protected route that returns the currently logged-in user.

    The frontend calls this route to check whether the saved token is valid.
    """
    return current_user