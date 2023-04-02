from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Self

__all__ = (
    'ModelType',
    'Status',
    'RelationshipType',
    'ChannelType',
)


class ModelType(Enum):
    """Enumeration of model types."""
    guild = 0
    user = 1
    channel = 2
    message = 3
    attachment = 4
    role = 5
    internal = 6
    unknown = 31

    @classmethod
    def _missing_(cls, value: Self) -> Self:
        return cls.unknown


class Status(Enum):
    """The status of a user's presence."""
    online = 'online'
    idle = 'idle'
    dnd = 'dnd'
    offline = 'offline'


class RelationshipType(Enum):
    """The type of a relationship."""
    friend = 'friend'
    outgoing_request = 'outgoing_request'
    incoming_request = 'incoming_request'
    blocked = 'blocked'

    # Aliases
    outgoing = outgoing_request
    incoming = incoming_request


class ChannelType(Enum):
    """The type of a channel."""
    text = 'text'
    announcement = 'announcement'
    voice = 'voice'
    category = 'category'
    dm = 'dm'
    group = 'group'

    @property
    def is_guild(self) -> bool:
        return self in (self.text, self.announcement, self.voice, self.category)

    @property
    def is_dm(self) -> bool:
        return self in (self.dm, self.group)

    @property
    def is_text_based(self) -> bool:
        return self in (self.text, self.announcement, self.dm, self.group)

    @property
    def is_voice_based(self) -> bool:
        return self is self.voice
