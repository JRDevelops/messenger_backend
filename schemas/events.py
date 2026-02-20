from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from enums import EventStatus

#related to event details
class EventBase(BaseModel):
  chat_id: int
  event_name: str = Field(min_length=1, max_length=50)
  event_date: datetime 

class EventCreate(EventBase):
  pass

class EventResponse(EventBase):
  model_config = ConfigDict(from_attributes=True)

  event_id: int

class EventUpdate(BaseModel):
  event_name: str | None = Field(min_length=1, max_length=50, default=None)
  event_date: datetime | None = Field(default=None)

#related to event status
class EventStatusBase(BaseModel):
  event_id: int
  user_id: int
  status: EventStatus = Field(default=EventStatus.PENDING)

class EventStatusCreate(EventStatusBase):
  pass

class EventStatusResponse(EventStatusBase):
  pass

class EventStatusUpdate(BaseModel):
  status: EventStatus | None = Field(default=None)