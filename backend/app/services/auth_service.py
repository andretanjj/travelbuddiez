import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import BaseModel

from app.database import get_connection

# Reads JWT settings from env var
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256") #fallback to HS256 if var DNE
ACCESS_TOKEN_EXPIRY_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRY_MINUTES", "30")) #fallback to 1440 if var DNE

class Token(BaseModel):
    # Response model.
    access_token: str
    token_type: str


class TokenData(BaseModel):
    # Stores username in the JWT "sub" field.
    username: str | None = None


class User(BaseModel):
    # User information returned to the frontend.
    username: str
    email: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    # Internal database user model that includes the password hash.
    hashed_password: str


# FastAPI dependency that reads the token from Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Create a pw hasher using FastAPI pwdlib
password_hash = PasswordHash.recommended()

# If user DNE, helps avoid obvious timing differences.
DUMMY_HASH = password_hash.hash("dummypassword")

"""
HELPER FUNCTIONS
"""

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Checks whether the plain password matches the stored password hash.
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    # Hashes a plain password before saving it into Supabase.   
    return password_hash.hash(password)


def get_user_by_username_or_email(username_or_email):
    """
    Finds a user by username or email.
    Tutorial uses fake_users_db, TravelBuddiesz uses Supabase PostgreSQL query.
    """
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT
                username,
                email,
                hashed_password,
                disabled
            FROM users
            WHERE username = %s OR email = %s;
            """,
            (
                username_or_email,
                username_or_email.lower(),
            ),
        )

        user_row = cur.fetchone()

        if user_row is None:
            return None

        return UserInDB(**dict(user_row))

    finally:
        cur.close()
        conn.close()


def authenticate_user(username_or_email, password):
    # Checks whether the user exists and whether the password is correct.
    user = get_user_by_username_or_email(username_or_email)

    if user is None:
        # Still verify against dummy hash when user is missing.
        verify_password(password, DUMMY_HASH)
        return False

    if not verify_password(password, user.hashed_password):
        return False

    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    # Creates a signed JWT access token.
    if JWT_SECRET_KEY is None:
        raise ValueError("JWT_SECRET_KEY is missing from environment variables")

    to_encode = data.copy()

    if expires_delta is not None:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    # JWT expiry time.
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )

    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    # Decodes the JWT token and returns the logged-in user.
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if JWT_SECRET_KEY is None:
        raise ValueError("JWT_SECRET_KEY is missing from environment variables")

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        username = payload.get("sub")

        if username is None:
            raise credentials_exception

        token_data = TokenData(username=username)

    except InvalidTokenError:
        raise credentials_exception

    user = get_user_by_username_or_email(token_data.username)

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """
    Checks whether the current user is active.
    For now, most users will have disabled = false.
    """
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    return current_user


def create_user(username, email, password):
    # Creates a new user account in Supabase.
    existing_username = get_user_by_username_or_email(username)

    if existing_username is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken",
        )

    existing_email = get_user_by_username_or_email(email)

    if existing_email is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO users (username, email, hashed_password, disabled)
            VALUES (%s, %s, %s, %s)
            RETURNING username, email, disabled;
            """,
            (
                username,
                email.lower(),
                get_password_hash(password),
                False,
            ),
        )

        new_user = cur.fetchone()
        conn.commit()

        return User(**dict(new_user))

    except Exception as error:
        conn.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    finally:
        cur.close()
        conn.close()