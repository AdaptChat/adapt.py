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
    'MessageType',
)


class ModelType(Enum):
    """|enum|

    Enumeration of model types.

    Attributes
    ----------
    guild
        The model is a :class:`Guild`.
    user
        The model is a :class:`User`.
    channel
        The model is a :class:`Channel`.
    message
        The model is a :class:`Message`.
    attachment
        The model is an :class:`Attachment`.
    role
        The model is a :class:`Role`.
    internal
        The model is an internal model.
    unknown
        The model type is unknown.
    """
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
    """|enum|

    The status of a user's presence.

    Attributes
    ----------
    online
        The user is online.
    idle
        The user is idle.
    dnd
        The user is has enabled Do Not Disturb.
    offline
        The user is offline.
    """
    online = 'online'
    idle = 'idle'
    dnd = 'dnd'
    offline = 'offline'


class RelationshipType(Enum):
    """|enum|

    The type of a relationship.

    Attributes
    ----------
    friend
        The user is your friend.
    outgoing_request
        You have sent a friend request to the user.
    incoming_request
        You have received a friend request from the user.
    blocked
        You have blocked the user.
    """
    friend = 'friend'
    outgoing_request = 'outgoing_request'
    incoming_request = 'incoming_request'
    blocked = 'blocked'

    # Aliases
    outgoing = outgoing_request
    incoming = incoming_request


class ChannelType(Enum):
    """|enum|

    The type of a channel.

    Attributes
    ----------
    text
        The channel is a text channel.
    announcement
        The channel is an announcement channel.
    voice
        The channel is a voice channel.
    category
        The channel is a category channel.
    dm
        The channel is a DM channel.
    group
        The channel is a group DM channel.
    """
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


class MessageType(Enum):
    """|enum|

    default
        A normal message.
    join
        A join message, sent when a user joins either a group DM or a guild.
    leave
        A leave message, sent when a user leaves either a group DM or a guild.
    pin
        A message that indicates another message has been pinned.
    """
    default = 'default'
    join = 'join'
    leave = 'leave'
    pin = 'pin'
