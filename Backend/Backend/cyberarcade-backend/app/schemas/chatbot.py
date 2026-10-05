from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    lab_id: Optional[UUID] = None


class ChatMessageResponse(BaseModel):
    message_id: UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageResponse]
    lab_id: Optional[UUID]
