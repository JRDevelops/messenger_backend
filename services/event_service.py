from typing import Annotated

from auth import CurrentUser, hash_password, verify_password
from fastapi import HTTPException, status, Depends
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

import models
from database import get_db 
from schemas import EventCreate

class EventService():
  def __init__(self, db: Annotated[AsyncSession,Depends(get_db)]):
    self.db = db

  async def create_event(self, current_user: CurrentUser, event_create: EventCreate):
    #check if user is a member of the chat
    current_member = await self.member_of_chat(current_user.user_id, event_create.chat_id)
    #create a chat
    new_event = models.Events(
      chat_id = event_create.chat_id,
      event_name = event_create.event_name,
      event_date = event_create.event_date
    )

    self.db.add(new_event)
    await self.db.commit()
    await self.db.refresh(new_event)

    return new_event

  #non API call functions
  async def member_of_chat(self, user_id: int, chat_id: int):
    result = await self.db.execute(select(models.ChatMembers).where(
        and_(
          models.ChatMembers.chat_id == chat_id,
          models.ChatMembers.user_id == user_id
        )
      )
    )
    member = result.scalars().first()
    if not member:
      raise HTTPException(
        status_code = status.HTTP_403_FORBIDDEN,
        detail="user is not a member of the chat."
      )

    return member
