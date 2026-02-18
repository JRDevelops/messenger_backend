from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import Base, engine

from routers import users, contacts, chats

#create the database if it does not exist
@asynccontextmanager
async def lifespan(_app: FastAPI):
  # startup
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
  yield
  # shutdown
  await engine.dispose()

#start API
app = FastAPI(lifespan=lifespan)
#app = FastAPI()

#setup router
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(contacts.router, prefix="/api/contacts", tags=["contacts"])
app.include_router(chats.router, prefix="/api/chats", tags=["chats"])

print("Loading completed.")




  
  