from __future__ import annotations

from typing import TYPE_CHECKING

from .asset import Asset
from .bitflags import UserFlags
from .channel import Messageable
from .enums import ChannelType
from .object import AdaptObject
from ..util import deprecated, find, MISSING

if TYPE_CHECKING:
    from typing import Any, Self

    from .channel import DMChannel
    from .enums import RelationshipType
    from ..connection import Connection
    from ..types.user import ClientUser as RawClientUser, User as RawUser
    from ..util import IOSource

__all__ = ('ClientUser', 'PartialUser', 'User', 'Relationship')


class BaseUser:
    if TYPE_CHECKING:
        _connection: Connection
        username: str
        discriminator: int
        _avatar: str | None
        _banner: str | None
        bio: str | None
        _flags: int

    def _update(self, data: RawUser) -> None:
        self.username = data['username']
        self.discriminator = data['discriminator']
        self._avatar = data['avatar']
        self._banner = data['banner']
        self.bio = data['bio']
        self._flags = data['flags']

    if TYPE_CHECKING:
        @property
        def id(self) -> int:
            raise NotImplementedError

    @property
    @deprecated(
        use='username',
        reason='This property is officially named "username" and it is a good practice to use that instead of "name".',
    )
    def name(self) -> str:
        """:class:`str`: The user's username. This is an alias for :attr:`username`.

        .. deprecated:: 0.1.0
            This property is officially named :attr:`username` and it is a good practice to use that instead of "name".
        """
        return self.username

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
        return Asset(connection=self._connection, url=self._avatar)

    @property
    def banner(self) -> Asset:
        """:class:`.Asset`: The user's banner."""
        return Asset(connection=self._connection, url=self._banner)

    @property
    def flags(self) -> UserFlags:
        """:class:`.UserFlags`: The user's flags."""
        return UserFlags(self._flags)

    @property
    def is_bot(self) -> bool:
        """:class:`bool`: Whether the user is a bot account."""
        return self.flags.bot

    def __str__(self) -> str:
        return self.tag

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} id={self.id!r} username={self.username!r} '
            f'discriminator={self.discriminator!r}>'
        )

    def __format__(self, format_spec: str) -> str:
        if format_spec == 'd':
            return self.display_name
        elif format_spec == 'u':
            return self.username
        elif format_spec == '@':
            return self.mention

        return self.tag.__format__(format_spec)


class ClientUser(BaseUser, AdaptObject):
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

    __slots__ = (
        '_connection',
        'username',
        'discriminator',
        '_avatar',
        '_banner',
        'bio',
        '_flags',
        'email',
    )

    if TYPE_CHECKING:
        email: str

    def __init__(self, *, connection: Connection, data: RawClientUser) -> None:
        self._connection = connection
        self._update(data)

    def _update(self, data: RawClientUser) -> None:
        super()._update(data)
        self._id = data['id']
        self.email = data['email']

    async def edit(
        self,
        *,
        username: str = MISSING,
        avatar: IOSource | None = MISSING,
        banner: IOSource | None = MISSING,
        bio: IOSource | None = MISSING,
    ) -> Self:
        """|coro|

        Updates the client's user information. Only the parameters passed will be updated.

        Parameters
        ----------
        username: :class:`str`
            The new username to use.
        avatar: :class:`bytes`, path-like object, file-like object, or ``None``
            The new avatar to use. If ``None``, the avatar will be removed.
        banner: :class:`bytes`, path-like object, file-like object, or ``None``
            The new banner to use. If ``None``, the banner will be removed.
        bio: :class:`str` or ``None``
            The new bio to use. If ``None``, the bio will be removed.

        Returns
        -------
        :class:`.ClientUser`
            The updated client user.
        """
        self._update(await self._connection.http.edit_authenticated_user(
            username=username,
            avatar=avatar,
            banner=banner,
            bio=bio,
        ))
        return self

    async def delete(self, *, password: str) -> None:
        """|coro|

        Deletes the client's user account. This is irreversible.

        .. note::
            The account must be a user account; if it is a bot account, the bot account can only be deleted by the
            user account that owns it.

        Parameters
        ----------
        password: :class:`str`
            The password of the user, required for security purposes.

        Raises
        ------
        TypeError
            The client user is a bot account.
        """
        if self.is_bot:
            raise TypeError('Cannot delete a bot account.')
        await self._connection.http.delete_authenticated_user(password=password)


class PartialUser(AdaptObject, Messageable):
    """A partial user object which operates with only an ID.

    This is useful for performing operations on users without having to fetch them first.
    """

    __slots__ = ('_connection', '_dm_channel')

    def __init__(self, *, connection: Connection, id: int) -> None:
        self._id = id
        self._connection = connection
        self._dm_channel: DMChannel | None = None

    def _update(self, data: dict) -> None:
        if id := data.get('id'):
            self._id = id

    @property
    def dm_channel(self) -> DMChannel | None:
        """:class:`.DMChannel`: The DM channel with this user, if it exists in the cache."""
        if channel := self._dm_channel:
            return channel

        if found := find(
            self._connection._dm_channels.values(),
            lambda dm: dm.type is ChannelType.dm and dm.recipient == self,
        ):
            self._dm_channel = found
            return found

    async def create_dm(self) -> DMChannel:
        """|coro|

        Creates a DM channel with this user. This makes the API call despite whether a DM channel already exists.

        Returns
        -------
        :class:`.DMChannel`
            The DM channel created.
        """
        channel = await self._connection.http.create_user_dm_channel(self.id)
        self._dm_channel = resolved = self._connection.add_raw_dm_channel(channel)
        return resolved

    async def _get_channel(self) -> DMChannel:
        if self.dm_channel is None:
            await self.create_dm()
        return self.dm_channel

    @property
    def relationship(self) -> Relationship | None:
        """:class:`.Relationship`: The relationship between you and this user.

        Returns ``None`` if no relationship exists.
        """
        return self._connection.get_relationship(self.id)

    async def accept_friend_request(self) -> Relationship:
        """|coro|

        Accepts the incoming friend request from this user.

        Returns
        -------
        :class:`.Relationship`
            The relationship created from accepting the friend request.

        Raises
        ------
        TypeError
            If there is no incoming friend request from this user.
        """
        if self.relationship.type is not RelationshipType.incoming:
            raise TypeError('No incoming friend request from this user')

        relationship = await self._connection.http.accept_friend_request(self.id)
        return self._connection.update_raw_relationship(relationship)

    async def block(self) -> Relationship:
        """|coro|

        Blocks this user.

        Returns
        -------
        :class:`.Relationship`
            The relationship created from blocking the user.
        """
        relationship = await self._connection.http.block_user(self.id)
        return self._connection.update_raw_relationship(relationship)

    async def _delete_relationship_if_of_type(self, type: RelationshipType) -> None:
        if self.relationship is not None and self.relationship.type is type:
            await self.relationship.delete()

    async def unblock(self) -> None:
        """|coro|

        Unblocks this user. This is a checked-equivalent of :meth:`.Relationship.delete`.

        Raises
        ------
        TypeError
            If this user is not blocked.
        """
        await self._delete_relationship_if_of_type(RelationshipType.blocked)

    async def revoke_friend_request(self) -> None:
        """|coro|

        Revokes the outgoing friend request to this user. This is a checked-equivalent of
        :meth:`.Relationship.delete`.

        Raises
        ------
        TypeError
            If there is no outgoing friend request to this user.
        """
        await self._delete_relationship_if_of_type(RelationshipType.outgoing)

    async def decline_friend_request(self) -> None:
        """|coro|

        Declines the incoming friend request from this user. This is a checked-equivalent of
        :meth:`.Relationship.delete`.

        Raises
        ------
        TypeError
            If there is no incoming friend request from this user.
        """
        await self._delete_relationship_if_of_type(RelationshipType.incoming)

    async def remove_friend(self) -> None:
        """|coro|

        Removes this user as a friend. This is a checked-equivalent of :meth:`.Relationship.delete`.

        Raises
        ------
        TypeError
            If this user is not a friend.
        """
        await self._delete_relationship_if_of_type(RelationshipType.friend)


class User(BaseUser, PartialUser):
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

    __slots__ = (
        'username',
        'discriminator',
        '_avatar',
        '_banner',
        'bio',
        '_flags',
    )

    def __init__(self, *, connection: Connection, data: RawUser) -> None:
        super().__init__(connection=connection, id=data['id'])
        self._update(data)

    def _update(self, data: RawUser) -> None:
        BaseUser._update(self, data)

    async def send_friend_request(self) -> Relationship:
        """|coro|

        Sends a friend request to this user.

        Returns
        -------
        :class:`.Relationship`
            The relationship created from sending the friend request.
        """
        relationship = await self._connection.http.send_friend_request(
            username=self.username,
            discriminator=self.discriminator,
        )
        return self._connection.update_raw_relationship(relationship)


class Relationship:
    """Represents a relationship between you, the client user, and another user."""

    __slots__ = ('_connection', '_user_id', '_type')

    def __init__(self, *, connection: Connection, user_id: int, type: RelationshipType) -> None:
        self._connection = connection
        self._user_id = user_id
        self._type = type

    @property
    def user(self) -> User:
        """:class:`.User`: The user that this relationship is with."""
        return self._connection.get_user(self._user_id)

    @property
    def type(self) -> RelationshipType:
        """:class:`.RelationshipType`: The type of this relationship."""
        return self._type

    async def delete(self) -> None:
        """|coro|

        Deletes this relationship:

        - If the relationship type is ``friend``, this will unfriend the user.
        - If the relationship type is ``outgoing_request``, this will cancel the outgoing friend request.
        - If the relationship type is ``incoming_request``, this will decline the incoming friend request.
        - If the relationship type is ``blocked``, this will unblock the user.
        """
        await self._connection.http.delete_relationship(self._user_id)

    async def accept(self) -> Self:
        """|coro|

        Accepts this relationship if it is an incoming friend request. This is equivalent to calling
        :meth:`.User.accept_friend_request`.

        Returns
        -------
        :class:`.Relationship`
            The relationship created from accepting the friend request.

        Raises
        ------
        TypeError
            If the relationship type is not ``incoming_request``.
        """
        return await self.user.accept_friend_request()

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} user={self.user!r} type={self.type!r}>'

    @property
    def _key(self) -> tuple[int, RelationshipType]:
        return self._user_id, self._type

    def __hash__(self) -> int:
        return hash(self._key)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and other._key == self._key
