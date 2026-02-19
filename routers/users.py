from typing import Annotated

from auth import CurrentUser
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import status, Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db 
from schemas import Token, UserCreate, UserPublic, UserPrivate, UserUpdate, UserUpdatePassword
from services import UserService, AuthService

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
  service = UserService(db)
  new_user = await service.create_user(user)
  return new_user

#authenticate user
@router.post("/token", response_model=Token)
async def login_for_access_token(
  form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
  db: Annotated[AsyncSession, Depends(get_db)]
):
  service = AuthService(db)
  token = await service.auth_user(form_data)
  return token

#get current logged in user
@router.get(
    "/me",
    response_model = UserPrivate
)
async def get_current_user(
  current_user: CurrentUser
):
  return current_user

#Get public details for a user
@router.get(
  "/{user_id}",
  response_model=UserPublic
)
async def get_user_public(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
  service = UserService(db)
  user = await service.get_user_public(user_id)
  return user


#update password
@router.patch(
    "/me/password",
    response_model=UserPrivate
)
async def update_user_password(
  passwords: UserUpdatePassword,
  db: Annotated[AsyncSession,Depends(get_db)],
  current_user: CurrentUser
):
  service = UserService(db)
  await service.update_password(current_user, passwords)
  return current_user

#update user details
@router.patch(
    "/me", 
    response_model=UserPrivate 
)
async def update_user(current_user: CurrentUser, user_update: UserUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
  service = UserService(db)
  updated_user = await service.update_user(current_user,user_update)
  return updated_user

#delete a user
@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_user(current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
  await db.delete(current_user)
  await db.commit()



