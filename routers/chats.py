from typing import Annotated

from auth import CurrentUser
from fastapi import status, Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db 
from services import ChatService
from schemas import ChatResponse, ChatCreate, ChatUpdate, ChatMembersResponse, ChatMembersCreate, ChatMembersUpdate

from enums import ChatRole

router = APIRouter()

print("Loading in chats API...")

### API related to chats and chat members

#create a new group chat
@router.post(
  "",
  response_model=ChatResponse
)
async def create_chat(chat_details: ChatCreate, current_user: CurrentUser, db: Annotated[AsyncSession,Depends(get_db)]):
  service = ChatService(db)
  new_chat = await service.create_chat(chat_details, current_user)
  await service.add_chat_member(new_chat.chat_id, current_user.user_id, ChatRole.OWNER)
  return new_chat


#recieve info about a chat
@router.get(
  "/{chat_id}",
  response_model=ChatResponse
)
async def get_chat(current_user: CurrentUser, chat_id: int, db: Annotated[AsyncSession,Depends(get_db)]):
  service = ChatService(db)
  #check if user is authorised to see info about the chat
  await service.get_user_in_chat(chat_id, current_user.user_id)
  chat = await service.get_chat_info(chat_id)
  return chat

#recieve chat members
@router.get(
    "/{chat_id}/members",
    response_model=list[ChatMembersResponse]
)
async def get_chat_members(current_user: CurrentUser, chat_id: int, db: Annotated[AsyncSession,Depends(get_db)]):
  service = ChatService(db)
  #check if user is authorised to see info about the chat
  await service.get_user_in_chat(chat_id, current_user.user_id)
  chat_members = await service.get_chat_members(chat_id)
  return chat_members

#update chat settings
@router.patch(
  "/{chat_id}",
  response_model=ChatResponse
)
async def update_chat(current_user: CurrentUser, chat_id: int, chat_updates: ChatUpdate, db: Annotated[AsyncSession,Depends(get_db)]):
  service = ChatService(db)
  #check if user is authorised to see info about the chat
  await service.get_user_in_chat(chat_id, current_user.user_id)
  updated_chat = await service.update_chat(chat_id, chat_updates)
  return updated_chat

#add a new member to an existing chat
@router.post(
  "/{chat_id}/{user_id}",
  response_model=ChatMembersResponse
)
async def add_member(current_user: CurrentUser, new_chat_member: ChatMembersCreate, db: Annotated[AsyncSession,Depends(get_db)]):
  service = ChatService(db)
  current_user_has_access_to_chat = await service.get_user_in_chat(new_chat_member.chat_id, current_user.user_id)
  new_member = await service.add_chat_member(new_chat_member.chat_id, new_chat_member.user_id, new_chat_member.role)
  return new_member

#remove a member from a group
@router.delete(
  "/{chat_id}/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_member(current_user: CurrentUser, chat_id: int, user_id: int, db: Annotated[AsyncSession,Depends(get_db)]):
  service = ChatService(db)
  await service.delete_member(current_user, chat_id, user_id)


#delete a chat - Only called by a group admin
@router.delete(
  "/{chat_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_chat(current_user: CurrentUser, chat_id: int, db: Annotated[AsyncSession,Depends(get_db)]):
  service = ChatService(db)
  await service.delete_chat_as_admin(current_user, chat_id)

#update chat member role
@router.patch(
  "/{chat_id}/{user_id}/updaterole",
  response_model=ChatMembersResponse
)
async def update_member_role(current_user: CurrentUser, chat_id: int, user_id: int, updated_data: ChatMembersUpdate, db: Annotated[AsyncSession,Depends(get_db)]):
  service = ChatService(db)
  updated_member = await service.update_member_role(current_user, chat_id, user_id, updated_data)
  return updated_member

