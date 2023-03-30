from typing import TypeAlias

from . import channel, guild, presence, role, user, ws

Snowflake: TypeAlias = int
Timestamp: TypeAlias = str

del TypeAlias
