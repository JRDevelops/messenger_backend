from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr

from enums import ContactStatus

#User related 
class UserBase(BaseModel):
  username: str = Field(min_length=1, max_length=50)
  email : EmailStr = Field(max_length=100)

class UserCreate(UserBase):
  password : str = Field(min_length=8, max_length=100) #input password as text, will be saved to database as a password_hash

class UserPublic(BaseModel):
  model_config = ConfigDict(from_attributes=True)
  
  user_id: int
  display_name: str | None 
  profile_picture_url: str | None
  status_message: str | None 
  last_seen_at: datetime

class UserPrivate(UserPublic):
  user_id: int
  username: str = Field(min_length=1, max_length=50)
  email : EmailStr = Field(max_length=100)
  created_at: datetime
  is_active: bool
  is_verified: bool
  contacts : list[ContactResponse]
  in_contacts : list[ContactResponse]

class UserUpdate(BaseModel):
  display_name: str | None = Field(default = None)
  profile_picture_url: str | None = Field(default = None)
  status_message: str | None = Field(default = None)
  last_seen_at: datetime = Field(default = None)
  is_active: bool = Field(default = None)
  is_verified: bool = Field(default = None)

class UserUpdatePassword(BaseModel):
  password : str = Field(min_length=8, max_length=100) #input password as text, will be saved to database as a password_hash

class Token(BaseModel):
  access_token: str
  token_type: str

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
  

