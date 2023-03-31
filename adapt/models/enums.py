from enum import Enum


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
