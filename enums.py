from enum import Enum

class ContactStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    BLOCKED = "blocked"

class ChatType(str, Enum):
    DIRECT = "direct"
    GROUP = "group"

class EventStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"