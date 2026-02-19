from typing import Annotated

from auth import CurrentUser, hash_password, verify_password
from fastapi import HTTPException, status, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import models
from database import get_db 
from schemas import UserCreate, UserUpdatePassword, UserUpdate

class UserService():
  def __init__(self, db: Annotated[AsyncSession,Depends(get_db)]):
    self.db = db

  #create a new user
  async def create_user(self, user: UserCreate):
    #check that username is unique
    result = await self.db.execute(select(models.User).where(func.lower(models.User.username) == user.username.lower()))
    user_exists = result.scalars().first()
    if user_exists:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Username already exists"
      )
    
    #check if email is unique
    result = await self.db.execute(select(models.User).where(func.lower(models.User.email) == user.email.lower()))
    email_exists = result.scalars().first()
    if email_exists:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Email already exists"
      )
    
    new_user = models.User(
      username=user.username,
      email = user.email.lower(),
      password_hash = hash_password(user.password)
    )

    #confirm all to database
    self.db.add(new_user)
    await self.db.commit()
    await self.db.refresh(new_user)

    return new_user
  
  #update user password;
  async def update_password(self, current_user: CurrentUser, passwords: UserUpdatePassword):
    #even though user is authenticated - check password again to ensure no one has gained access to the device
    correct_password = verify_password(passwords.old_password, current_user.password_hash)
    if not correct_password:
      raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          details = "incorrect password"
        )

    #check that the given passwords match
    if passwords.new_password1 != passwords.new_password2:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="new passwords do not match"
        )
    
    #create password hash
    new_password_hash = hash_password(passwords.new_password1)

    current_user.password_hash = new_password_hash

    await self.db.commit()
    await self.db.refresh(current_user)

    return current_user
  
  #get a users public details
  async def get_user_public(self, user_id: int):
    result = await self.db.execute(
      select(models.User)
      .where(models.User.user_id == user_id)
    )
    user = result.scalars().first()
    if not user:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
      )
    return user
  
  #update details about a user
  async def update_user(self, current_user: CurrentUser, user_update: UserUpdate):
    #update user details
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
      setattr(current_user, field, value)
    
    await self.db.commit() 
    await self.db.refresh(current_user)

    return current_user
