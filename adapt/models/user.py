from __future__ import annotations

from typing import TYPE_CHECKING

from .asset import Asset
from .object import AdaptObject

if TYPE_CHECKING:
    from ..connection import Connection
    from ..types.user import ClientUser as RawClientUser, User as RawUser

__all__ = ('ClientUser', 'User')


class BaseUser(AdaptObject):
    __slots__ = (
        '_connection',
        'username',
        'discriminator',
        '_avatar',
        '_banner',
        'bio',
        '_flags',
    )

    if TYPE_CHECKING:
        username: str
        discriminator: int
        _avatar: str | None
        _banner: str | None
        bio: str | None
        _flags: int

    def __init__(self, *, connection: Connection, data: RawUser) -> None:
        self._connection = connection
        self._update(data)

    def _update(self, data: RawUser) -> None:
        self._id = data['id']
        self.username = data['username']
        self.discriminator = data['discriminator']
        self._avatar = data['avatar']
        self._banner = data['banner']
        self.bio = data['bio']
        self._flags = data['flags']

    @property
    def padded_discriminator(self) -> str:
        """:class:`str`: The user's discriminator with leading zeros."""
        return f'{self.discriminator:0>4}'

    @property
    def tag(self) -> str:
        """:class:`str`: The user's tag. (``username#discriminator``)"""
        return f'{self.username}#{self.padded_discriminator}'

    @property
    def mention(self) -> str:
        """:class:`str`: The string used to mention the user. (``<@id>``)"""
        return f'<@{self.id}>'

    @property
    def display_name(self) -> str:
        """:class:`str`: The name displayed to refer to the user.

        This is the same as :attr:`username` for users. For members, this is overridden to return the member's nickname
        (or username if the member has no nickname).
        """
        return self.username

    @property
    def avatar(self) -> Asset:
        """:class:`.Asset`: The user's avatar."""
        return Asset(connection=self._connection, route=f'/avatars/{self.id}/{self._avatar}', uuid=self._avatar)

    @property
    def banner(self) -> Asset:
        """:class:`.Asset`: The user's banner."""
        return Asset(connection=self._connection, route=f'/banners/{self.id}/{self._banner}', uuid=self._banner)

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} id={self.id!r} username={self.username!r} '
            f'discriminator={self.discriminator!r}>'
        )

    def __format__(self, format_spec: str):
        if format_spec == 'd':
            return self.display_name
        elif format_spec == 'u':
            return self.username
        elif format_spec == 'm':
            return self.mention
        else:
            return self.tag


class ClientUser(BaseUser):
    """Represents the user object for the client user.

    Attributes
    ----------
    username: :class:`str`
        The user's username.
    discriminator: :class:`int`
        The user's discriminator.
    bio: :class:`str`
        The user's custom bio.
    email: :class:`str`
        The user's email.
    """

    __slots__ = ('email',)

    if TYPE_CHECKING:
        email: str

    def __init__(self, *, connection: Connection, data: RawClientUser) -> None:
        super().__init__(connection=connection, data=data)
        self._update(data)

    def _update(self, data: RawClientUser) -> None:
        super()._update(data)
        self.email = data['email']


class User(BaseUser):
    """Represents an Adapt user.

    Attributes
    ----------
    username: :class:`str`
        The user's username.
    discriminator: :class:`int`
        The user's discriminator.
    bio: :class:`str`
        The user's custom bio.
    """

    __slots__ = ()

    def __init__(self, *, connection: Connection, data: RawUser) -> None:
        super().__init__(connection=connection, data=data)
