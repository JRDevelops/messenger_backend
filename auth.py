from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

import models
from config import settings
from database import get_db

#Hash using Argon2 - automatically adds salt
password_hash = PasswordHash.recommended()

#points to login route
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/token")

#function to hash the password
def hash_password(password: str) -> str:
  return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
  return password_hash.verify(plain_password, hashed_password)

#create an access token
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
  """Create a JWT access token."""
  to_encode = data.copy()
  if expires_delta:
    expire = datetime.now(UTC) + expires_delta
  else:
    expire = datetime.now(UTC) + timedelta(
      minutes=settings.access_token_expire_minutes
    )
  to_encode.update({"exp": expire})
  encoded_jwt = jwt.encode(
    to_encode,
    settings.secret_key.get_secret_value(),
    algorithm=settings.algorithm
  )

  return encoded_jwt

#verify an access token
def verify_access_token(token: str) -> str | None:
  """verify a JWT access token and return the subject (user id) if valid"""
  try:
    payload = jwt.decode(
      token,
      settings.secret_key.get_secret_value(),
      algorithms=[settings.algorithm],
      options= {"require": ["exp","sub"]}
    )
  except jwt.InvalidTokenError:
    return None
  else:
    return payload.get("sub")
  
#create dependency to get current logged in user
async def get_current_user_dep(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> models.User:
  """Get the currently authenticated user."""
  user_id = verify_access_token(token)
  if user_id is None:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid or expired token",
      headers={"WWW-Authenticate": "Bearer"}
    )
  
  # validate user_id is a valid integer (defense against malformed JWT)
  try:
    user_id_int = int(user_id)
  except (TypeError, ValueError):
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid or expired token",
      headers={"WWW-Authenticate": "Bearer"}
    )
  
  result = await db.execute(
    select(models.User)
    .options( #eager load the columns which rely on a relationship with another table
      selectinload(models.User.contacts),
      selectinload(models.User.in_contacts)
    )
    .where(
      models.User.user_id == user_id_int
    )
  )
  user = result.scalars().first()

  if not user:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="User not found",
      headers={"WWW-Authenticate": "Bearer"}
    )

  return user

#alias for get_current_user
CurrentUser = Annotated[models.User, Depends(get_current_user_dep)]