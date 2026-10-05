from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.chatbot import ChatbotConversation
from app.schemas.chatbot import ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse
from app.services.ai_service import get_chatbot_response

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    req: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message to the AI chatbot and receive a response."""

    # Persist user message
    user_msg = ChatbotConversation(
        user_id=current_user.user_id,
        lab_id=req.lab_id,
        role="user",
        content=req.message,
    )
    db.add(user_msg)
    await db.flush()

    # Fetch recent conversation history for this user (and lab if provided)
    history_query = (
        select(ChatbotConversation)
        .where(ChatbotConversation.user_id == current_user.user_id)
        .order_by(ChatbotConversation.created_at.desc())
        .limit(20)
    )
    if req.lab_id:
        history_query = history_query.where(ChatbotConversation.lab_id == req.lab_id)
    history_result = await db.execute(history_query)
    history_rows = list(reversed(history_result.scalars().all()))

    conversation_history = [
        {"role": row.role, "content": row.content}
        for row in history_rows
        if row.message_id != user_msg.message_id  # exclude the message we just added
    ]

    # Call AI provider — gracefully degrade on failure
    try:
        ai_text = await get_chatbot_response(
            user_message=req.message,
            lab_id=req.lab_id,
            conversation_history=conversation_history,
        )
    except RuntimeError as exc:
        ai_text = str(exc)
    except Exception:
        ai_text = "An unexpected error occurred. Please try again."

    # Persist assistant response
    assistant_msg = ChatbotConversation(
        user_id=current_user.user_id,
        lab_id=req.lab_id,
        role="assistant",
        content=ai_text,
    )
    db.add(assistant_msg)
    await db.flush()
    await db.refresh(assistant_msg)
    await db.commit()

    return ChatMessageResponse(
        message_id=assistant_msg.message_id,
        role="assistant",
        content=ai_text,
        created_at=assistant_msg.created_at,
    )


@router.get("/history", response_model=ChatHistoryResponse)
async def get_history(
    lab_id: Optional[UUID] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get conversation history for the current user."""
    query = (
        select(ChatbotConversation)
        .where(ChatbotConversation.user_id == current_user.user_id)
    )
    if lab_id:
        query = query.where(ChatbotConversation.lab_id == lab_id)

    query = query.order_by(ChatbotConversation.created_at.desc()).limit(limit)
    result = await db.execute(query)
    messages = list(reversed(result.scalars().all()))

    return ChatHistoryResponse(
        messages=[
            ChatMessageResponse(
                message_id=m.message_id,
                role=m.role,
                content=m.content,
                created_at=m.created_at,
            )
            for m in messages
        ],
        lab_id=lab_id,
    )
