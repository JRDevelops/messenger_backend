from typing import Annotated

from fastapi import APIRouter, FastAPI, HTTPException, status, Depends
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

import models
from database import Base, engine, get_db 
from schemas import ContactCreate, ContactResponse, ContactUpdateStatus

from auth import CurrentUser

router = APIRouter()


print("Loading in contacts API...")

### Contacts ###

#Get contacts of a user
@router.get(
  "/me",
  response_model=list[ContactResponse]
)
async def get_contacts(current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
  #check if user has contacts
  contacts_result = await db.execute(select(models.Contact).where(models.Contact.user_id == current_user.user_id))
  contacts = contacts_result.scalars().all()

  if not contacts:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="User does not have any contacts"
    )

  return contacts

@router.post(
  "",
  response_model=ContactCreate,
)
async def create_contact(
  contact: ContactCreate, 
  current_user: CurrentUser, 
  db: Annotated[AsyncSession, Depends(get_db)]
):
  
  #check if contact exists
  contact_result = await db.execute(select(models.User).where(models.User.user_id == contact.contact_id))
  contact_exists = contact_result.scalars().first()
  if not contact_exists:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="New contact ID does not exist"
    )
  
  #check contact is already in users contacts
  already_a_contact_result = await db.execute(
    select(models.Contact)
    .where(
      and_(
        models.Contact.user_id == current_user.user_id,
        models.Contact.contact_id == contact.contact_id
      )
    )
  )
  already_a_contact = already_a_contact_result.scalars().first()
  if already_a_contact:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="New contact ID already exists in users contacts"
    )
  
  
  #check user is not adding themselves
  if current_user.user_id == contact.contact_id:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="User ID cannot equal the new contact ID"
    )

  new_contact = models.Contact(
    user_id = current_user.user_id,
    contact_id = contact.contact_id,
    status = "pending"
  )

  db.add(new_contact)
  await db.commit()
  await db.refresh(new_contact)

  return new_contact
  
@router.patch(
  "/{user_id}/{contact_id}",
  response_model=ContactResponse
)
async def update_contact_status(current_user: CurrentUser, contact_update: ContactUpdateStatus, db: Annotated[AsyncSession, Depends(get_db)]):
  
  #check if user has that contact
  contact_result = await db.execute(
    select(models.Contact)
    .where(
      and_(
        models.Contact.user_id == current_user.user_id,
        models.Contact.contact_id == contact_update.contact_id
      )
    )
  )
  contact = contact_result.scalars().first()

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

  await db.commit()
  await db.refresh(contact)
	
  return contact

#delete a contact
@router.delete(
    "/{user_id}/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_contact(current_user: CurrentUser, contact_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
  
  #check if contact exists
  contact_result = await db.execute(
    select(models.Contact)
    .where(
      and_(
        models.Contact.user_id == current_user.user_id,
        models.Contact.contact_id == contact_id
      )
    )
  )
  contact = contact_result.scalars().first()

  if not contact:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="Contact not found"
    )
  
  await db.delete(contact)
  await db.commit()