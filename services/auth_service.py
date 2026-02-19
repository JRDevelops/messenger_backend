from typing import Annotated

from auth import create_access_token, verify_password
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import HTTPException, status, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import models
from config import settings
from database import get_db 
from schemas import Token

class AuthService():
  def __init__(self, db: Annotated[AsyncSession,Depends(get_db)]):
    self.db = db

  #Authenticate user and return access token
  async def auth_user(self, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    # lookup user by email (case-insensitive)
    # Note: OAuth2PasswordRequestForm uses "username" field, but we are treating as email
    result = await self.db.execute(
      select(models.User).where(
        func.lower(models.User.email) == form_data.username.lower()
      )
    )
    user = result.scalars().first()

    # verify user exists and password is correct
    # don't reveal which one failed (best practice)
    if not user or not verify_password(form_data.password, user.password_hash):
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"}
      )
    
    # create access token with user id as subject
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
      data={"sub": str(user.user_id)}, 
      expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")