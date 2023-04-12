from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .enums import ChannelType
from .message import Message
from .object import AdaptObject

if TYPE_CHECKING:
    from typing import Self, TypeAlias

    from .guild import Guild
    from .user import User
    from ..connection import Connection
    from ..types.channel import GuildChannel as RawGuildChannel, DMChannel as RawDMChannel

__all__ = (
    'Messageable',
    'PartialMessageable',
    'GuildChannel',
    'TextChannel',
    'AnnouncementChannel',
    'PrivateChannel',
    'DMChannel',
)


class Messageable(ABC):
    """Represents a channel or model that can be a medium for text-based communication."""

    __slots__ = ()

    _connection: Connection

    @abstractmethod
    async def _get_channel(self) -> MessageableChannel:
        raise NotImplementedError

    async def fetch_message(self, message_id: int) -> Message:
        """|coro|

        Fetches a message from the channel.

        Parameters
        ----------
        message_id: :class:`int`
            The ID of the message to fetch.

        Returns
        -------
        :class:`.Message`
            The message that was fetched.
        """
        channel = await self._get_channel()
        return Message(channel=channel, data=await self._connection.http.get_message(channel.id, message_id))

    async def send(self, content: str | None = None, *, nonce: str | None = None) -> Message:
        """|coro|

        Sends a message to the channel.

        Parameters
        ----------
        content: :class:`str`
            The content of the message to send.
        nonce: :class:`str`
            An optional nonce for integrity. When this message is received through the websocket, the nonce will be
            included in the message payload. This can be used to verify that the message was sent successfully.

        Returns
        -------
        :class:`.Message`
            The message that was sent.
        """
        channel = await self._get_channel()
        return Message(
            channel=channel,
            data=await self._connection.http.create_message(channel.id, content=content, nonce=nonce),
        )


class PartialMessageable(Messageable):
    """Represents a channel tha t can be a medium for text-based communication that operates with only its channel ID.

    This is useful for performing messaging operations on channels without having to fetch them first or guarantee
    that they are cached.

    Attributes
    ----------
    channel_id: :class:`int`
        The ID of the channel.
    """

    __slots__ = ('_connection', 'channel_id')

    def __init__(self, *, connection: Connection, channel_id: int) -> None:
        self._connection = connection
        self.channel_id = channel_id

    async def _get_channel(self) -> Self:
        return self


class GuildChannel(AdaptObject, ABC):
    """Represents a guild channel in Adapt.

    This is the base class for all types of guild channels, and should not be used directly.

    Channels are the primary way to communicate with other users in Adapt. They can be either text-based, voice-based,
    or a category of channels.

    Attributes
    ----------
    type: :class:`.ChannelType`
        The type of the channel. :attr:`.ChannelType.is_guild` for this value will always be ``True``.
    guild: :class:`.Guild`
        The guild that the channel belongs to.
    parent_id: :class:`int` | None
        The ID of the parent category that the channel belongs to, if any.
    name: :class:`str`
        The name of the channel.
    position: :class:`int`
        The position of the channel in the channel list. See the
        `essence documentation <https://github.com/AdaptChat/essence/blob/main/src/models/channel.rs#L183-L204>`_
        for more information.
    """

    # TODO: channel overwrites and permission checks
    __slots__ = (
        'type',
        'guild',
        'parent_id',
        'name',
        'position',
    )

    _connection: Connection

    if TYPE_CHECKING:
        type: ChannelType
        guild: Guild
        parent_id: int | None
        name: str
        position: int

    def _update(self, data: RawGuildChannel) -> None:
        self._id = data['id']
        self.type = ChannelType(data['type'])
        self.parent_id = data['parent_id']
        self.name = data['name']
        self.position = data['position']

    async def delete(self) -> None:
        """|coro|

        Deletes the channel. You must have the :attr:`~.Permissions.manage_channels` permission to do this.
        """
        await self._connection.http.delete_channel(self.id)


class TextChannel(GuildChannel, Messageable):
    """Represents a text-based guild channel in Adapt.

    Attributes
    ----------
    topic: :class:`str` | None
        The topic of the channel, if any.
    nsfw: :class:`bool`
        Whether the channel is NSFW.
    locked: :class:`bool`
        Whether the channel is locked. Only people with the :attr:`~.Permissions.manage_channels` permission can send
        messages in locked channels.
    """

    __slots__ = ('_connection', 'topic', 'nsfw', 'locked', '_slowmode')

    if TYPE_CHECKING:
        _connection: Connection
        topic: str | None
        nsfw: bool
        locked: bool
        _slowmode: int

    def __init__(self, *, guild: Guild, data: RawGuildChannel) -> None:
        self._connection = guild._connection
        self.guild = guild
        self._update(data)

    def _update(self, data: RawGuildChannel) -> None:
        super()._update(data)
        self.topic = data['topic']
        self.nsfw = data['nsfw']
        self.locked = data['locked']
        self._slowmode = data['slowmode']

    @property
    def slowmode(self) -> float:
        """:class:`float`: The slowmode of the channel, in seconds. This is ``0.0`` if the channel has no slowmode."""
        return self._slowmode / 1000.0

    @property
    def slowmode_ms(self) -> int:
        """:class:`int`: The slowmode of the channel, in milliseconds. This is ``0`` if the channel has no slowmode."""
        return self._slowmode

    @property
    def is_nsfw(self) -> bool:
        """:class:`bool`: Whether the channel is NSFW.

        This is an alias for :attr:`~.TextBasedGuildChannel.nsfw`. and is provided for consistency.
        """
        return self.nsfw

    @property
    def is_locked(self) -> bool:
        """:class:`bool`: Whether the channel is locked.

        This is an alias for :attr:`~.TextBasedGuildChannel.locked`. and is provided for consistency.
        """
        return self.locked

    @property
    def mention(self) -> str:
        """:class:`str`: A string that allows you to mention the channel."""
        return f'<#{self.id}>'

    async def _get_channel(self) -> Self:
        return self

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} name={self.name!r}>'


class AnnouncementChannel(TextChannel):
    """Represents an announcement channel in a guild in Adapt."""

    __slots__ = ()


def _guild_channel_factory(*, guild: Guild, data: RawGuildChannel) -> GuildChannel:
    channel_type = ChannelType(data['type'])

    if channel_type is ChannelType.text:
        factory = TextChannel
    elif channel_type is ChannelType.announcement:
        factory = AnnouncementChannel
    else:
        # TODO
        factory = GuildChannel

    return factory(guild=guild, data=data)


class PrivateChannel(AdaptObject, ABC):
    """Represents a DM or group channel in Adapt.

    This is the base class for all types of private channels, and should not be used directly.

    Attributes
    ----------
    type: :class:`.ChannelType`
        The type of the channel. Can be either :attr:`~.ChannelType.dm` or :attr:`~.ChannelType.group`.
        :attr:`.ChannelType.is_dm` for this value will always be ``True``.
    """

    __slots__ = ('type', 'recipient_ids')

    _connection: Connection

    if TYPE_CHECKING:
        type: ChannelType
        me: User
        recipient_ids: list[int]

    def _update(self, data: RawDMChannel) -> None:
        self._id = data['id']
        self.type = ChannelType(data['type'])
        self.recipient_ids = data['recipient_ids']

    @property
    @abstractmethod
    def can_manage(self) -> bool:
        """:class:`bool`: Whether the client can manage the channel."""
        raise NotImplementedError

    @property
    def recipients(self) -> list[User]:
        """:class:`list`[:class:`.User`]: The recipients of the channel, including yourself.

        This is a shortcut for calling :meth:`.Connection.get_user` with each ID in :attr:`~.PrivateChannel.recipient_ids`.
        Users that are not cached will be excluded from the list.
        """
        return [user for user in map(self._connection.get_user, self.recipient_ids) if user is not None]

    async def delete(self) -> None:
        """|coro|

        Deletes the channel.
        """
        if not self.can_manage:
            raise Exception('oregon')  # TODO: raise Forbidden error

        await self._connection.http.delete_channel(self.id)


class DMChannel(PrivateChannel, Messageable):
    """Represents a DM channel in Adapt.

    Attributes
    ----------
    type: :class:`.ChannelType`
        The type of the channel. :attr:`~.ChannelType.is_dm` for this value will always be ``True``.
    """

    __slots__ = ('_connection',)

    def __init__(self, *, connection: Connection, data: RawDMChannel) -> None:
        self._connection = connection
        self._update(data)

    @property
    def can_manage(self) -> bool:
        """:class:`bool`: Whether the client can manage the channel.

        This will always be ``True`` for DM channels.
        """
        return True

    @property
    def recipient_id(self) -> int:
        """:class:`int`: The ID of the other recipient of this DM channel."""
        self_id = self._connection.http.client_id
        return next(id for id in self.recipient_ids if id != self_id)

    @property
    def recipient(self) -> User | None:
        """:class:`.User`: The other recipient of this DM channel.

        This is a shortcut for calling :meth:`.Connection.get_user` with :attr:`~.DMChannel.recipient_id`. If the user
        is not cached, this will return ``None``.
        """
        return self._connection.get_user(self.recipient_id)

    async def _get_channel(self) -> Self:
        return self

    def __repr__(self) -> str:
        return f'<DMChannel id={self.id} recipient_id={self.recipient_id}>'


if TYPE_CHECKING:
    MessageableChannel: TypeAlias = TextChannel | PrivateChannel | PartialMessageable
