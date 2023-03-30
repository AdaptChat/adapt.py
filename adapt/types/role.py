from __future__ import annotations

from typing import TypedDict

from . import Snowflake

__all__ = ('PermissionPair', 'Role')


class PermissionPair(TypedDict):
    allow: int
    deny: int


class Role(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    name: str
    color: int | None
    pemissions: PermissionPair
    position: int
    flags: int
