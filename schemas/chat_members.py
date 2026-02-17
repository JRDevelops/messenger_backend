from __future__ import annotations

from datetime import datetime, time
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Time

from enums import EventStatus

#schemas related to the chat members table
#this table holds info regarding who is a member of a particular chat and their role etc.

class ChatMembersBase(BaseModel):
  chat_id: int
  user_id: int
  is_admin: bool 

#add a member to a group
class ChatMembersCreate(ChatMembersBase):
  pass

#recieve info about a member in a group
class ChatMembersResponse(ChatMembersBase):
  id: int
  event_status: EventStatus | None = Field(default=None)
  muted_until: datetime | None = Field(default=None)
  created_at: datetime

#update user role or event related status
class ChatMembersUpdate(BaseModel):
  chat_id: int
  user_id: int
  is_admin: bool | None = Field(default=None)
  event_status: EventStatus | None = Field(default=None)
  muted_until: datetime | None = Field(default=None)