from __future__ import annotations

from typing import TypedDict

from . import Snowflake, Timestamp
from .channel import GuildChannel
from .role import Role
from .user import User

__all__ = (
    'Member',
    'GuildMemberCount',
    'PartialGuild',
    'Guild',
)


class Member(User):
    guild_id: Snowflake
    nick: str | None
    roles: list[Snowflake] | None
    joined_at: Timestamp


class GuildMemberCount(TypedDict):
    total: int
    online: int | None


class EditOwnMemberPayload(TypedDict, total=False):
    nick: str | None


class EditMemberPayload(TypedDict, total=False):
    nick: str | None
    roles: list[Snowflake] | None


class PartialGuild(TypedDict):
    id: int
    name: str
    description: str | None
    icon: str | None
    banner: str | None
    owner_id: int
    flags: int
    member_count: GuildMemberCount | None
    vanity_url: str | None


class Guild(PartialGuild):
    members: list[Member] | None
    roles: list[Role] | None
    channel: list[GuildChannel] | None


class _CreateGuildPayloadRequired(TypedDict):
    name: str


class CreateGuildPayload(_CreateGuildPayloadRequired, total=False):
    description: str | None
    icon: str | None
    banner: str | None
    public: bool
    nonce: str | None


class EditGuildPayload(TypedDict, total=False):
    name: str | None
    description: str | None
    icon: str | None
    banner: str | None
    public: bool | None


class DeleteGuildPayload(TypedDict):
    password: str
