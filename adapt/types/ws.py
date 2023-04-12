from __future__ import annotations

from typing import Generic, Literal, TypedDict, TypeAlias, TypeVar

from . import Snowflake
from .channel import Channel, DMChannel
from .guild import Guild, Member, PartialGuild
from .message import Message
from .presence import Presence
from .role import Role
from .user import ClientUser, User, Relationship

E = TypeVar('E', bound=str)
D = TypeVar('D', bound=TypedDict)
T = TypeVar('T')

__all__ = (
    'ReadyEvent',
    'UserUpdateEvent',
    'GuildUpdateEvent',
    'ChannelUpdateEvent',
    'RoleUpdateEvent',
    'MemberUpdateEvent',
    'PresenceUpdateEvent',
    'UserDeleteEvent',
    'GuildCreateEvent',
    'MemberRemoveType',
    'GuildRemoveEvent',
    'MessageCreateEvent',
    'InboundMessage',
)


class _InboundEvent(TypedDict, Generic[E]):
    event: E


class _InboundEventWithData(_InboundEvent[E], Generic[E, D]):
    data: D


class ReadyEvent(TypedDict):
    session_id: str
    user: ClientUser
    guilds: list[Guild]
    dm_channels: list[DMChannel]
    presences: list[Presence]
    relationships: list[Relationship]
    
    
class _UpdateEvent(TypedDict, Generic[T]):
    before: T
    after: T


UserUpdateEvent: TypeAlias = _UpdateEvent[User]
GuildUpdateEvent: TypeAlias = _UpdateEvent[PartialGuild]
ChannelUpdateEvent: TypeAlias = _UpdateEvent[Channel]
RoleUpdateEvent: TypeAlias = _UpdateEvent[Role]
MemberUpdateEvent: TypeAlias = _UpdateEvent[Member]
PresenceUpdateEvent: TypeAlias = _UpdateEvent[Presence]


class UserDeleteEvent(TypedDict):
    user_id: Snowflake
    
    
class GuildCreateEvent(TypedDict):
    guild: Guild
    nonce: str | None


MemberRemoveType: TypeAlias = Literal['delete', 'leave', 'kick', 'ban']


class _MemberRemoveInfoRequired(TypedDict):
    type: MemberRemoveType


class _MemberRemoveInfo(_MemberRemoveInfoRequired, total=False):
    moderator_id: Snowflake


class GuildRemoveEvent(_MemberRemoveInfo):
    guild_id: Snowflake


class MessageCreateEvent(TypedDict):
    message: Message
    nonce: str | None


# harmony -> adapt.py, this is modeled as **OutboundMessage** in essence!
InboundMessage: TypeAlias = (
    _InboundEvent[Literal['hello', 'ping', 'pong']]
    | _InboundEventWithData[Literal['ready'], ReadyEvent]
    | _InboundEventWithData[Literal['user_update'], UserUpdateEvent]
    | _InboundEventWithData[Literal['user_delete'], UserDeleteEvent]
    | _InboundEventWithData[Literal['channel_update'], ChannelUpdateEvent]
    | _InboundEventWithData[Literal['role_update'], RoleUpdateEvent]
    | _InboundEventWithData[Literal['member_update'], MemberUpdateEvent]
    | _InboundEventWithData[Literal['presence_update'], PresenceUpdateEvent]
    | _InboundEventWithData[Literal['guild_create'], GuildCreateEvent]
    | _InboundEventWithData[Literal['guild_update'], GuildUpdateEvent]
    | _InboundEventWithData[Literal['guild_remove'], GuildRemoveEvent]
    | _InboundEventWithData[Literal['message_create'], MessageCreateEvent]
)
