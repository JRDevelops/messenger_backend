from typing import Annotated

from fastapi import APIRouter, FastAPI, HTTPException, status, Depends
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

import models
from database import Base, engine, get_db 
from schemas import ContactCreate, ContactResponse, ContactUpdateStatus

router = APIRouter()


print("Loading in contacts API...")

### Contacts ###

#Get contacts of a user
@router.get(
  "/{user_id}",
  response_model=list[ContactResponse]
)
async def get_contacts(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
  #check if user exists and has contacts
  user_exists_result = await db.execute(select(models.User).where(models.User.user_id == user_id))
  user_exists = user_exists_result.scalars().first()
  contacts_result = await db.execute(select(models.Contact).where(models.Contact.user_id == user_id))
  contacts = contacts_result.scalars().all()

  if not user_exists:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="User does not exist"
    )
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
async def create_contact(contact: ContactCreate, db: Annotated[AsyncSession, Depends(get_db)]):
  #check if user exists
  user_result = await db.execute(select(models.User).where(models.User.user_id == contact.user_id))
  user_exists = user_result.scalars().first()
  if not user_exists:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="User ID does not exist"
    )
  
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
        models.Contact.user_id == contact.user_id,
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
  if contact.user_id == contact.contact_id:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="User ID cannot equal the new contact ID"
    )

  
  new_contact = models.Contact(
    user_id = user_exists.user_id,
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
async def update_contact_status(user_id: int, contact_id: int, contact_update: ContactUpdateStatus, db: Annotated[AsyncSession, Depends(get_db)]):
  #check if user exists 
  user_result = await db.execute(select(models.User).where(models.User.user_id == user_id))
  user = user_result.scalars().first()

  if not user:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="User not found"
    )
  #check if user has that contact
  contact_result = await db.execute(
    select(models.Contact)
    .where(
      and_(
        models.Contact.user_id == user_id,
        models.Contact.contact_id == contact_id
      )
    )
  )
  contact = contact_result.scalars().first()

  if not contact:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="User does not have a contact with that username"
    )
  
  #check that status is valid
  if contact_update.status not in ["pending", "accepted", "blocked"]: 
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST, 
      detail="Invalid status value" 
    )

  #otherwise update the status
  update_data = contact_update.model_dump(exclude_unset=True)
  for field, value in update_data.items():
    setattr(contact, field, value)

  await db.commit()
  await db.refresh(contact)
	
  return contact

#delete a contact
@router.delete(
    "/{user_id}/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_contact(user_id: int, contact_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
  #check if user exists 
  user_result = await db.execute(select(models.User).where(models.User.user_id == user_id))
  user = user_result.scalars().first()

  if not user:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="User not found"
    )
  
  #check if contact exists
  contact_result = await db.execute(
    select(models.Contact)
    .where(
      and_(
        models.Contact.user_id == user_id,
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