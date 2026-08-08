from datetime import datetime

from pydantic import BaseModel


class SaveAiResponseRequest(BaseModel):
    title: str | None = None
    user_message: str
    ai_response: str


class SavedAiResponse(BaseModel):
    id: int
    title: str | None
    user_message: str
    ai_response: str
    created_at: datetime