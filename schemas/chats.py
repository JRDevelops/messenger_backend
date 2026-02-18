from __future__ import annotations

from datetime import datetime, time
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Time

from enums import ChatType

#schemas related to creating or updating group chats and 1 to 1 chats
#does not include members of the chat or info about messages sent

#Base schema
class ChatBase(BaseModel):
  chat_name : str = Field(min_length=1, max_length=100)
  chat_type : ChatType = Field(default=ChatType.GROUP)

#create a new chat
class ChatCreate(ChatBase):
  pass

#recieve info about a chat
class ChatResponse(ChatBase):
  model_config = ConfigDict(from_attributes=True)

  chat_id : int
  chat_picture_url : str | None = Field(default=None)

  event_name: str | None = Field(max_length=50)
  event_date: datetime | None = Field(default=None)

  default_name: str | None = Field(default=None,max_length=50)
  default_time: time | None = Field(default=None)
  default_weekday: int | None = Field(default=None, ge=1, le=7)

  created_at: datetime

#update info about a chat
class ChatUpdate(BaseModel):
  chat_name : str | None = Field(default=None, min_length=1, max_length=100)
  chat_picture_url : str | None = Field(default=None)

  event_name: str | None = Field(default=None,max_length=50)
  event_date: datetime | None = Field(default=None)

  default_name: str | None = Field(default=None,max_length=50)
  default_time: time | None = Field(default=None)
  default_weekday: int | None = Field(default=None, ge=1, le=7)