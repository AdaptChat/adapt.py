from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Self

__all__ = ('ModelType', 'Status')


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
