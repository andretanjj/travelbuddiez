from fastapi import HTTPException, status

from app.database import get_connection


def get_user_id_by_username(username: str) -> int:
    """
    Resolves the database user ID from the username stored in the JWT.
    """

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT id
            FROM users
            WHERE username = %s;
            """,
            (username,),
        )

        user_row = cur.fetchone()

        if user_row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user_row["id"]

    finally:
        cur.close()
        conn.close()