from typing import Annotated

from auth import CurrentUser
from fastapi import status, Depends, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db 
from services import EventService
from schemas import EventResponse, EventCreate

router = APIRouter()

#API calls related to events and members event status

@router.post(
  "",
  response_model = EventResponse
)
async def create_event(new_event: EventCreate, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
  service = EventService(db)
  new_event = await service.create_event(current_user, new_event)
  return new_event
