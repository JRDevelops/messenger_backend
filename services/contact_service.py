from typing import Annotated

from auth import CurrentUser
from fastapi import HTTPException, status, Depends
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

import models
from database import get_db 
from schemas import ContactUpdateStatus

class ContactService():

  def __init__(self, db: Annotated[AsyncSession,Depends(get_db)]):
    self.db = db

  #get the contact list from the database
  async def get_user_contacts(self, current_user: CurrentUser):
    #check if user has contacts
    contacts_result = await self.db.execute(select(models.Contact).where(models.Contact.user_id == current_user.user_id))
    contacts = contacts_result.scalars().all()

    return contacts
  
  #create a new contact
  async def create_contact(self, current_user: CurrentUser, contact_id: int):
    #check if contact exists as a user
    contact_result = await self.db.execute(select(models.User).where(models.User.user_id == contact_id))
    contact_exists = contact_result.scalars().first()
    if not contact_exists:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="New contact ID does not exist"
      )
    
    #check contact is already in users contacts
    already_a_contact = await self.get_contact(current_user.user_id, contact_id)
    if already_a_contact:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="New contact ID already exists in users contacts"
      )
    
    
    #check user is not adding themselves
    if current_user.user_id == contact_id:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="User ID cannot equal the new contact ID"
      )

    new_contact = models.Contact(
      user_id = current_user.user_id,
      contact_id = contact_id,
      status = "pending"
    )

    self.db.add(new_contact)
    await self.db.commit()
    await self.db.refresh(new_contact)

    return new_contact
  
  #check new status and update contact
  async def update_contact_status(self, current_user: CurrentUser, contact_update: ContactUpdateStatus):
    contact = await self.get_contact(current_user.user_id, contact_update.contact_id)

    if not contact:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User does not have a contact with that user ID"
      )
    
    #check that status is valid
    if contact_update.status not in ["pending", "accepted", "blocked"]: 
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, 
        detail="Invalid status value" 
      )
    
    #update the status
    contact.status = contact_update.status

    await self.db.commit()
    await self.db.refresh(contact)

    return contact
  
  #delete a contact
  async def delete_contact(self, user_id: int, contact_id: int):
    contact = await self.get_contact(user_id, contact_id)

    if not contact:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User does not have a contact with that user ID"
      )
    
    await self.db.delete(contact)
    await self.db.commit()

  #retrieve a contact
  async def get_contact(self, user_id: int, contact_id: int):
    #check if user has that contact
    contact_result = await self.db.execute(
      select(models.Contact)
      .where(
        and_(
          models.Contact.user_id == user_id,
          models.Contact.contact_id == contact_id
        )
      )
    )
    contact = contact_result.scalars().first()
    return contact