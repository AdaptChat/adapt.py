from __future__ import annotations

from typing import Literal, TypedDict, TypeAlias

from . import Snowflake
from .role import PermissionPair

__all__ = (
    'GuildChannelType',
    'CreateGuildChannelPayload',
    'CreateDMChannelPayload',
    'DMChannelType',
    'ChannelType',
    'PermissionOverwrite',
    'GuildChannel',
    'DMChannel',
    'Channel',
)


GuildChannelType: TypeAlias = Literal['text', 'announcement', 'voice', 'category']
DMChannelType: TypeAlias = Literal['dm', 'group']
ChannelType: TypeAlias = GuildChannelType | DMChannelType


class _CreateGuildChannelPayloadRequired(TypedDict):
    type: GuildChannelType
    name: str
    icon: str | None
    parent_id: Snowflake | None
    overwrites: list[PermissionOverwrite] | None


class CreateGuildChannelPayload(_CreateGuildChannelPayloadRequired, total=False):
    # Text, Announcement
    topic: str | None
    icon: str | None
    # Voice
    user_limit: int


class _GuildChannelRequired(TypedDict):
    type: GuildChannelType
    id: Snowflake
    guild_id: Snowflake
    name: str
    position: int
    overwrites: list[PermissionOverwrite]
    parent_id: Snowflake | None


class GuildChannel(_GuildChannelRequired, total=False):
    # TextBasedGuildChannelInfo
    topic: str | None
    nsfw: bool
    locked: bool
    slowmode: int
    # GuildChannelInfo::Voice
    user_limit: int


class PermissionOverwrite(PermissionPair):
    id: Snowflake


class _CreateDMChannelPayloadRequired(TypedDict):
    type: DMChannelType


class CreateDMChannelPayload(_CreateDMChannelPayloadRequired, total=False):
    # DM
    recipient_id: Snowflake
    # Group DM
    name: str
    recipient_ids: list[Snowflake]


class _DMChannelRequired(TypedDict):
    type: DMChannelType
    id: Snowflake
    recipient_ids: list[Snowflake]


class DMChannel(_DMChannelRequired, total=False):
    # Group DM
    name: str
    topic: str | None
    icon: str | None
    owner_id: Snowflake


Channel: TypeAlias = GuildChannel | DMChannel
