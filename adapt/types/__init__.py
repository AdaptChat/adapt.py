from typing import TypeAlias

from . import channel, guild, message, presence, role, user, ws

Snowflake: TypeAlias = int
Timestamp: TypeAlias = str

del TypeAlias
