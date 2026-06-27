from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import ChatCreate, ChatResponse, ChatHistoryResponse
from app.services.auth_service import get_current_user
from app.services.chat_service import ChatService

router = APIRouter()

@router.post("", response_model=ChatResponse)
async def chat(
    chat_in: ChatCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    chat_service = ChatService(db)
    chat_log = await chat_service.chat(current_user.id, chat_in.message)
    return ChatResponse(
        message=chat_log.message,
        response=chat_log.response,
        created_at=chat_log.created_at
    )

@router.get("/history", response_model=List[ChatHistoryResponse])
async def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    chat_service = ChatService(db)
    return await chat_service.get_history(current_user.id)
