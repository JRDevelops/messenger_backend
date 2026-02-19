from typing import Annotated

from auth import CurrentUser
from fastapi import HTTPException, status, Depends
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

import models
from database import get_db 
from schemas import ChatCreate, ChatUpdate, ChatMembersCreate, ChatMembersUpdate

from enums import ChatRole

class ChatService():

  def __init__(self, db: Annotated[AsyncSession,Depends(get_db)]):
    self.db = db

  #creates new chats, groups and 1 to 1
  async def create_chat(self, chat_details: ChatCreate, current_user: CurrentUser):

    #create a new chat
    new_chat = models.Chats(
      chat_name = chat_details.chat_name,
      chat_type = chat_details.chat_type
    )

    #add chat to table
    self.db.add(new_chat)
    await self.db.flush() #no need to commit as the commit will come once the initial member is added
    await self.db.refresh(new_chat)

    return new_chat

  #find a chat and return it from the database
  async def get_chat_info(self, chat_id: int):
  
    result = await self.db.execute(select(models.Chats).where(models.Chats.chat_id == chat_id))
    chat = result.scalars().first()
    return chat
  
  #update chat settings and event infomation
  async def update_chat(self, chat_id: int, chat_updates:ChatUpdate):
    #get the current chat
    result = await self.db.execute(select(models.Chats).where(models.Chats.chat_id == chat_id))
    current_chat = result.scalars().first()
    
    #create the updates
    update_data = chat_updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_chat, field, value)

    await self.db.commit()
    await self.db.refresh(current_chat)

    return current_chat
  
  #admin calls to delete the chat
  async def delete_chat_as_admin(self, current_user: CurrentUser, chat_id: int):
    await self.is_admin(chat_id, current_user.user_id)
    await self.delete_chat(chat_id)

  #add a new chat member to an existing group
  async def add_chat_member(self, chat_id: int, user_id: int, role: ChatRole):

    #check if member is already in the group
    result = await self.db.execute(select(models.ChatMembers).where(
        and_(
          models.ChatMembers.chat_id == chat_id,
          models.ChatMembers.user_id == user_id
        )
      )
    )
    new_user_exist = result.scalars().first()
    if new_user_exist:
      raise HTTPException(
        status_code = status.HTTP_400_BAD_REQUEST,
        detail="User already exists as a member in chat"
      )

    #add member to the group
    new_member = models.ChatMembers(
      chat_id = chat_id,
      user_id = user_id,
      role = role
    )
    self.db.add(new_member)
    await self.db.commit()
    await self.db.refresh(new_member)

    return new_member

  #find a user in a chat and return it from the database
  async def get_user_in_chat(self, chat_id: int, user_id: int):
    #check that the current user is a member for the current group
    result = await self.db.execute(
      select(models.ChatMembers).where(
        and_(
          models.ChatMembers.chat_id == chat_id,
          models.ChatMembers.user_id == user_id
        )
      )
    )
    user_in_chat = result.scalars().first()
    if not user_in_chat:
      raise HTTPException(
          status_code = status.HTTP_403_FORBIDDEN,
          detail="User does not have access to this chat"
        )

    return user_in_chat
  
  #send a list of chat members
  async def get_chat_members(self, chat_id: int):
    result = await self.db.execute(select(models.ChatMembers).where(models.ChatMembers.chat_id == chat_id))
    chat_members = result.scalars().all()
    return chat_members
  
  #delete a member from a chat
  async def delete_member(self, current_user: CurrentUser, chat_id: int, user_id: int):
    #check if user is an admin, or if deleting self
    if (not await self.is_admin(chat_id, current_user.user_id) and current_user.user_id != user_id):
      raise HTTPException(
          status_code = status.HTTP_403_FORBIDDEN,
          detail="User does not have permission."
        )
    user_to_delete = await self.get_user_in_chat(chat_id, user_id)
    await self.db.delete(user_to_delete)

    #check if chat_members_list is empty:
    chat_members = await self.get_chat_members(chat_id)
    if not chat_members:
      #list is empty so delete the group
      await self.delete_chat(chat_id)

    await self.db.commit()

  #update a members role in a chat
  #Only those with admin powers can do this. 
  #there must be at least 1 admin or owner role 
  async def update_member_role(self, current_user: CurrentUser, chat_id: int, user_id: int, updated_data: ChatMembersUpdate):

    #check if user is current owner
    is_owner = await self.is_owner(chat_id, current_user.user_id)
    if not is_owner:
      raise HTTPException(
          status_code = status.HTTP_403_FORBIDDEN,
          detail="User does not have permission."
        )
    
    chat_member = await self.get_user_in_chat(chat_id, user_id)
    current_member = await self.get_user_in_chat(chat_id, current_user.user_id)
    
    #owner cannot update their own role, as must first give away the owner role
    if current_user.user_id == user_id and current_member.role == ChatRole.OWNER:
      raise HTTPException(
          status_code = status.HTTP_400_BAD_REQUEST,
            detail="Ownership must be given to another member before users own role can be changed"
        )

    #check the new role is not the same as the original
    if chat_member.role == updated_data.role:
      raise HTTPException(
          status_code = status.HTTP_400_BAD_REQUEST,
          detail="New role must be different than old role."
        )

    #for updating admin or member roles
    if updated_data.role in (ChatRole.ADMIN,ChatRole.MEMBER):
      #update the role
      chat_member.role = updated_data.role
    #only the owner can assign another owner. Original ownership is lost
    elif updated_data.role == ChatRole.OWNER:
      #assign new owner
      chat_member.role = ChatRole.OWNER
      #make original owner an admin
      current_member.role = ChatRole.ADMIN

    #apply the update
    await self.db.commit()
    await self.db.refresh(chat_member)

    return chat_member

  #non api methods  

  #is user a group admin or owner?
  async def is_admin(self, chat_id: int, user_id: int) -> bool:
    user = await self.get_user_in_chat(chat_id, user_id)
    if user.role == ChatRole.OWNER or user.role == ChatRole.ADMIN:
      return True
    else:
      return False
    
  #is user a group owner?
  async def is_owner(self, chat_id: int, user_id: int) -> bool:
    user = await self.get_user_in_chat(chat_id, user_id)
    if user.role == ChatRole.OWNER:
      return True
    else:
      return False

  #delete a group
  async def delete_chat(self, chat_id: int):
    chat = await self.get_chat_info(chat_id)
    print(f"Deleting chat id {chat_id}")
    await self.db.delete(chat)
    await self.db.commit()

  


