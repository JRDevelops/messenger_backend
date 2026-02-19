from typing import Annotated

from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db 
from schemas import ContactCreate, ContactResponse, ContactUpdateStatus
from services import ContactService

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
  service = ContactService(db)
  contacts = await service.get_user_contacts(current_user)
  return contacts

#create a new contact
@router.post(
    "", 
    response_model=ContactCreate
)
async def create_contact(contact: ContactCreate, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
  service = ContactService(db)
  new_contact = await service.create_contact(current_user, contact.contact_id)
  return new_contact
  
#update an existing contact  
@router.patch(
  "/{user_id}/{contact_id}",
  response_model=ContactResponse
)
async def update_contact_status(current_user: CurrentUser, contact_update: ContactUpdateStatus, db: Annotated[AsyncSession, Depends(get_db)]):
  service = ContactService(db)
  contact = await service.update_contact_status(current_user, contact_update)
  return contact

#delete a contact
@router.delete(
    "/{user_id}/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_contact(current_user: CurrentUser, contact_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
  service = ContactService(db)
  await service.delete_contact(current_user.user_id, contact_id) 