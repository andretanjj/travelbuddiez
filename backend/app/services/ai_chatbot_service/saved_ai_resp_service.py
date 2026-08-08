from fastapi import HTTPException, status

from app.database import get_connection
from app.services.user_service import get_user_id_by_username


def save_ai_response_for_user(
    username: str,
    user_message: str,
    ai_response: str,
    title: str | None = None,
):
    """
    Saves one AI-generated response for the logged-in user.
    """

    user_id = get_user_id_by_username(username)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO saved_ai_responses (
                user_id,
                title,
                user_message,
                ai_response,
                saved_at
            )
            VALUES (
                %s, %s, %s, %s, NOW()
            )
            RETURNING *;
            """,
            (
                user_id,
                title,
                user_message,
                ai_response,
            ),
        )

        saved_response = cur.fetchone()
        conn.commit()

        return dict(saved_response)

    except Exception as error:
        conn.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    finally:
        cur.close()
        conn.close()

def get_saved_ai_responses_for_user(username: str):
    """
    Returns all AI responses saved by the logged-in user.
    """

    user_id = get_user_id_by_username(username)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT *
            FROM saved_ai_responses
            WHERE user_id = %s
            ORDER BY saved_at DESC;
            """,
            (user_id,),
        )

        return [
            dict(row)
            for row in cur.fetchall()
        ]

    finally:
        cur.close()
        conn.close()

def delete_saved_ai_response_for_user(
    username: str,
    saved_response_id: int,
):
    """
    Deletes one saved AI response belonging to the logged-in user.
    """

    user_id = get_user_id_by_username(username)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            DELETE FROM saved_ai_responses
            WHERE id = %s
              AND user_id = %s
            RETURNING id;
            """,
            (
                saved_response_id,
                user_id,
            ),
        )

        deleted_response = cur.fetchone()

        if deleted_response is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved AI response not found",
            )

        conn.commit()

        return {
            "message": "Saved AI response deleted successfully",
            "deletedId": deleted_response["id"],
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