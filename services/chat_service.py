from typing import Annotated

from auth import CurrentUser
from fastapi import HTTPException, status, Depends
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

import models
from database import get_db 
from schemas import ChatCreate

class ChatService():

  def __init__(self, db: Annotated[AsyncSession,Depends(get_db)]):
    self.db = db

  
  async def create_chat(self, chat_details: ChatCreate, current_user: CurrentUser):

    #create a new chat
    new_chat = models.Chats(
      chat_name = chat_details.chat_name,
      chat_type = chat_details.chat_type
    )

    #add chat to table
    self.db.add(new_chat)
    await self.db.flush() #no need to commit as the commit will come once the initial member is added
    await self.db.refresh(new_chat)

    return new_chat

  async def add_chat_member(self, chat: models.Chats, new_user: models.User, is_admin: bool):

    #check if member is already in the group
    result = await self.db.execute(select(models.ChatMembers).where(
        and_(
          models.ChatMembers.chat_id == chat.chat_id,
          models.ChatMembers.user_id == new_user.user_id
        )
      )
    )
    new_user_exist = result.scalars().first()
    if new_user_exist:
      raise HTTPException(
        status_code = status.HTTP_400_BAD_REQUEST,
        detail="User already exists as a member in chat"
      )

    #add member to the group
    new_member = models.ChatMembers(
      chat_id = chat.chat_id,
      user_id = new_user.user_id,
      is_admin = is_admin
    )
    self.db.add(new_member)
    await self.db.commit()
    await self.db.refresh(new_member)

    return new_member

  async def get_user_in_chat(self, chat_id: int, user_id: int):
    #check that the current user is a member for the current group
    result = await self.db.execute(
      select(models.ChatMembers).where(
        and_(
          models.ChatMembers.chat_id == chat_id,
          models.ChatMembers.user_id == user_id
        )
      )
    )
    user_in_chat = result.scalars().first()
    return user_in_chat

  async def get_chat_info(self, chat_id: int):
  
    result = await self.db.execute(select(models.Chats).where(models.Chats.chat_id == chat_id))
    chat = result.scalars().first()
    return chat