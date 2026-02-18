from typing import Annotated

from auth import CurrentUser
from datetime import timedelta
from fastapi import HTTPException, status, Depends, APIRouter
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db 
from services import ChatService
from schemas import ChatResponse, ChatCreate, ChatUpdate

router = APIRouter()

print("Loading in chats API...")

### API related to chats and chat members

#create a new group chat
@router.post(
  "",
  response_model=ChatResponse
)
async def create_chat(chat_details: ChatCreate, current_user: CurrentUser, db: Annotated[AsyncSession,Depends(get_db)]):
  service = ChatService(db)
  new_chat = await service.create_chat(chat_details, current_user)
  await service.add_chat_member(new_chat, current_user, True)

  return new_chat


#recieve info about a chat
@router.get(
  "/{chat_id}",
  response_model=ChatResponse
)
async def get_chat(current_user: CurrentUser, chat_id: int, db: Annotated[AsyncSession,Depends(get_db)]):
  services = ChatService(db)
  #check if user is authorised to see info about the chat
  is_current_user_in_chat = await services.get_user_in_chat(chat_id, current_user.user_id)

  if not is_current_user_in_chat:
    raise HTTPException(
        status_code = status.HTTP_403_FORBIDDEN,
        detail="User does not have access to this chat"
      )
  
  #otherwise get the chat
  chat = await services.get_chat_info(chat_id)
  
  return chat

#update chat settings
@router.patch(
  "/{chat_id}",
  response_model=ChatResponse
)
async def update_chat(current_user: CurrentUser, chat_updates: ChatUpdate, chat_id: int, db: Annotated[AsyncSession,Depends(get_db)]):
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

  print(user_in_chat.username)

  if not user_in_chat:
    raise HTTPException(
        status_code = status.HTTP_403_FORBIDDEN,
        detail="User does not have access to this chat"
      )
  
  #get the current chat
  result = await db.execute(select(models.Chats).where(models.Chats.chat_id == chat_id))
  current_chat = result.scalars().first()
  
  #create the updates
  update_data =chat_updates.model_dump(exclude_unset=True)
  for field, value in update_data.items():
      setattr(current_chat, field, value)

  await db.commit()
  await db.refresh(current_chat)

  return current_chat


#delete a chat --- possibly just delete the chat if the last member has been removed
