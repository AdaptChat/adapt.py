from __future__ import annotations

from typing import Literal, TypedDict, TypeAlias

from . import Snowflake, Timestamp

__all__ = (
    'PresenceStatus',
    'Device',
    'Presence',
)


PresenceStatus: TypeAlias = Literal['online', 'idle', 'dnd', 'offline']
Device: TypeAlias = Literal['desktop', 'mobile', 'web']


class Presence(TypedDict):
    user_id: Snowflake
    status: PresenceStatus
    custom_status: str | None
    devices: int
    online_since: Timestamp | None
