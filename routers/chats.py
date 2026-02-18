from typing import Annotated

from auth import CurrentUser
from fastapi import Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db 
from services import ChatService
from schemas import ChatResponse, ChatCreate, ChatUpdate

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
  await service.add_chat_member(new_chat, current_user, True)

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
  #otherwise get the chat
  chat = await service.get_chat_info(chat_id)
  
  return chat

#update chat settings
@router.patch(
  "/{chat_id}",
  response_model=ChatResponse
)
async def update_chat(current_user: CurrentUser, chat_id: int, chat_updates: ChatUpdate, db: Annotated[AsyncSession,Depends(get_db)]):
  service = ChatService(db)
  #check if user is authorised to see info about the chat
  await service.get_user_in_chat(chat_id, current_user.user_id)
  
  #update chat
  updated_chat = await service.update_chat(chat_id, chat_updates)

  return updated_chat


#delete a chat --- possibly just delete the chat if the last member has been removed
