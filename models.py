from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

#from enums import ContactStatus

print("Loading models...")

#define a user table
#this contains info about all users
class User(Base):
  __tablename__ = "users"

  user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  username: Mapped[str] =mapped_column(String(50), unique=True, nullable = False)
  email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
  password_hash: Mapped[str] = mapped_column(String(200), unique=False, nullable=False)
  display_name:Mapped[str | None] = mapped_column(String(50), nullable=True)
  profile_picture_url: Mapped[str | None] = mapped_column(String, nullable=True)
  status_message: Mapped[str | None] = mapped_column(String(200), nullable=True)
  last_seen_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
  is_active: Mapped[bool] = mapped_column(default=True)
  is_verified: Mapped[bool] = mapped_column(default=False)
  created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

  #used as a list of contacts to that the user has
  contacts: Mapped[list["Contact"]] = relationship(
    back_populates="user",
    cascade="all, delete-orphan",
    foreign_keys=lambda: [Contact.user_id],
    lazy="selectin"
  )
  #lists where they appear in others contacts
  in_contacts: Mapped[list["Contact"]] = relationship(
    back_populates="contact", 
    cascade="all, delete-orphan", 
    foreign_keys=lambda: [Contact.contact_id],
    lazy="selectin"
  ) 

#Authentications and sessions table to manage user logins and sessions

#contacts
class Contact(Base):
  __tablename__ = "contacts"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), nullable=False)
  contact_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), nullable=False)
  status: Mapped[str] = mapped_column(String(20), default="PENDING") #pending, accepted, blocked
  created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

  #relationships - ensures that if a user is deleted, their contacts are also deleted and vice versa
  user: Mapped["User"] = relationship(
    back_populates="contacts",
    foreign_keys=[user_id],
    lazy="selectin"
  )
  contact: Mapped["User"] = relationship(
    back_populates="in_contacts",
    foreign_keys=[contact_id],
    lazy="selectin"
  )



print("Models have loaded.")