from __future__ import annotations

from datetime import UTC, datetime, time

from sqlalchemy import DateTime, ForeignKey, Integer, String, Enum as SQLEnum, Time, Boolean
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

  #relationship with the group chat members table
  chat_member: Mapped[list["ChatMembers"]] = relationship(
    back_populates="user",
    cascade="all, delete-orphan",
    foreign_keys=lambda: [ChatMembers.user_id],
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

#chats - groups and 1 to 1 chats
class Chats(Base):
  __tablename__ = "chats"

  chat_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  chat_name: Mapped[str] = mapped_column(String(100), nullable=False)
  chat_type: Mapped[str] = mapped_column(String(20), nullable=False)
  chat_picture_url : Mapped[str | None] = mapped_column(String(200), nullable=True)

  #related to event
  #event_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
  #event_date: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

  #chat event setttings
  #default_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
  #default_time: Mapped[time | None] = mapped_column(Time, nullable=True)
  #default_weekday: Mapped[int | None] = mapped_column(Integer, nullable=True) #int 1 - 7 representing a weekday

  created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

  #relationship between the group table and the members table
  members: Mapped[list["ChatMembers"]] = relationship(
    back_populates="chat",
    cascade="all, delete-orphan",
    foreign_keys=lambda: [ChatMembers.chat_id],
    lazy="selectin"
  )


#chat members
class ChatMembers(Base):
  __tablename__ = "chat_members"

  id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
  chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.chat_id"), nullable=False)
  user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.user_id"), nullable=False)
  #is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
  role: Mapped[str] = mapped_column(String(20), default="member")
  #event_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
  muted_until: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
  created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

  #relationship bettern the chat id and the chat members
  chat: Mapped["Chats"] = relationship(
    back_populates="members",
    foreign_keys=[chat_id],
    lazy="selectin"
  )
  #relationship between the group member id and the user table id
  user: Mapped["User"] = relationship(
    back_populates="chat_member",
    foreign_keys=[user_id],
    lazy="selectin"
  )

print("Models have loaded.")