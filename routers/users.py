from typing import Annotated

from auth import create_access_token, hash_password, verify_password, CurrentUser
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import HTTPException, status, Depends, APIRouter
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from config import settings
from database import get_db 
from schemas import Token, UserCreate, UserPublic, UserPrivate, UserUpdate, UserUpdatePassword

router = APIRouter()

print("Loading in users API...")

### user database queries ###

#create a user
@router.post(
    "", 
    response_model=UserPrivate,
    status_code=status.HTTP_201_CREATED
)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
  #check that username is unique
  result = await db.execute(select(models.User).where(func.lower(models.User.username) == user.username.lower()))
  user_exists = result.scalars().first()
  if user_exists:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Username already exists"
    )
  #check if email is unique
  result = await db.execute(select(models.User).where(func.lower(models.User.email) == user.email.lower()))
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
  db.add(new_user)
  await db.commit()
  await db.refresh(new_user)

  return new_user

#authenticate user
@router.post("/token", response_model=Token)
async def login_for_access_token(
  form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
  db: Annotated[AsyncSession, Depends(get_db)]
):
  # lookup user by email (case-insensitive)
  # Note: OAuth2PasswordRequestForm uses "username" field, but we are treating as email
  result = await db.execute(
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

#get current logged in user
@router.get(
    "/me",
    response_model = UserPrivate
)
async def get_current_user(
  current_user: CurrentUser
):
  return current_user

#update password
#@router.patch(
#    "/me/password",
#    response_model=UserPrivate
#)
#async def update_user_password(
#  password: UserUpdatePassword,
#  db: Annotated[AsyncSession,Depends(get_db)],
#  current_user: UserPrivate = Depends(get_current_user)
#):
#  print("user is authenticated, new password is {password.password}")

#Get public details for a user
@router.get(
  "/{user_id}",
  response_model=UserPublic
)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
  result = await db.execute(
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

#Get private details for a user
@router.get("/details/me",
  response_model=UserPrivate
)
async def get_user_detailed(current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
  return current_user

#update user details
@router.patch(
    "/me", 
    response_model=UserPrivate 
)
async def update_user(current_user: CurrentUser, user_update: UserUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
  
  #update user details
  update_data = user_update.model_dump(exclude_unset=True)
  for field, value in update_data.items():
    setattr(current_user, field, value)
  
  await db.commit() 
  await db.refresh(current_user)

  return current_user

#delete a user
@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_user(current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
  
  await db.delete(current_user)
  await db.commit()



