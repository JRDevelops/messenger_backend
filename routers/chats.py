from typing import Annotated

from auth import CurrentUser
from datetime import timedelta
from fastapi import HTTPException, status, Depends, APIRouter
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db 
from schemas import ChatResponse, ChatCreate

router = APIRouter()

print("Loading in chats API...")

#create a new group chat
@router.post(
  "",
  response_model=ChatResponse
)
async def create_chat(chat_details: ChatCreate, current_user: CurrentUser, db: Annotated[AsyncSession,Depends(get_db)]):

  #create a new chat
  new_chat = models.Chats(
    chat_name = chat_details.chat_name,
    chat_type = chat_details.chat_type
  )

  #add chat to table
  db.add(new_chat)
  await db.commit()

  #add initial member to the group
  new_member = models.ChatMembers(
    chat_id = new_chat.chat_id,
    user_id = current_user.user_id,
    is_admin = True
  )
  db.add(new_member)
  await db.commit()

  await db.refresh(new_chat)
  await db.refresh(new_member)

  return new_chat

#recieve info about a chat
@router.get(
  "/{chat_id}",
  response_model=ChatResponse
)
async def get_chat(current_user: CurrentUser, chat_id: int, db: Annotated[AsyncSession,Depends(get_db)]):
  #check that the current user is a member for the current group
  result = await db.execute(
    select(models.ChatMembers).where(
      and_(
        models.ChatMembers.chat_id == chat_id,
        models.ChatMembers.user_id == current_user.user_id
      )
    )
  )
  user_in_chat = result.scalars().first()

  if not user_in_chat:
    raise HTTPException(
        status_code = status.HTTP_403_FORBIDDEN,
        detail="User does not have access to this chat"
      )
  
  #otherwise get the chat
  result = await db.execute(select(models.Chats).where(models.Chats.chat_id == chat_id))
  chat = result.scalars().first()
  
  return chat