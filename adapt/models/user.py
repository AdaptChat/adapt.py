from __future__ import annotations

from .object import AdaptObject


class PartialUser(AdaptObject):
    """A stateless partial user object. Once instantiated, it is immutable."""

    __slots__ = (
        'username',
        'discriminator',
        '_avatar',
        '_banner',
        'bio',
        'flags',
    )

    def __init__(self, ): ... # TODO
