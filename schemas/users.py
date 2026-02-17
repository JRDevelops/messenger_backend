from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr


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
  #contacts : list[ContactResponse]
  #in_contacts : list[ContactResponse]

class UserUpdate(BaseModel):
  display_name: str | None = Field(default = None)
  profile_picture_url: str | None = Field(default = None)
  status_message: str | None = Field(default = None)
  last_seen_at: datetime = Field(default = None)
  is_active: bool = Field(default = None)
  is_verified: bool = Field(default = None)

class UserUpdatePassword(BaseModel):
  old_password : str = Field(min_length=8, max_length=100) #old_password to confirm - want to make sure no one is updating that has access to already authorised app
  new_password1 : str = Field(min_length=8, max_length=100) #input password as text, will be saved to database as a password_hash
  new_password2 : str = Field(min_length=8, max_length=100) #compare against password1 to ensure that it is correct

class Token(BaseModel):
  access_token: str
  token_type: str