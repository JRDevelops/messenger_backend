from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr

from enums import ContactStatus


#contact list
class ContactBase(BaseModel):
  #user_id: int
  contact_id: int 

class ContactCreate(ContactBase):
  pass

class ContactResponse(ContactBase):
  model_config = ConfigDict(from_attributes=True)
  
  user_id: int
  status: ContactStatus | None = Field(default=ContactStatus.PENDING)
  created_at: datetime

class ContactUpdateStatus(BaseModel):
  contact_id: int
  status : str | None = Field(default=None,max_length=20)
  