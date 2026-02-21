from __future__ import annotations

from datetime import datetime, time
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Time

from enums import ChatRole

#schemas related to the chat members table
#this table holds info regarding who is a member of a particular chat and their role etc.

class ChatMembersBase(BaseModel):
  chat_id: int
  user_id: int
  role: ChatRole = Field(max_length=20, default=ChatRole.MEMBER) 

#add a member to a group
class ChatMembersCreate(ChatMembersBase):
  pass

#recieve info about a member in a group
class ChatMembersResponse(ChatMembersBase):
  id: int
  muted_until: datetime | None = Field(default=None)
  created_at: datetime

#update user role or mute status
class ChatMembersUpdate(BaseModel):
  role: ChatRole = Field(max_length=20, default=ChatRole.MEMBER) 
  muted_until: datetime | None = Field(default=None)