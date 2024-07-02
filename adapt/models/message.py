from __future__ import annotations

from typing import TYPE_CHECKING

from .bitflags import MessageFlags
from .embed import Embed
from .enums import MessageType
from .object import AdaptObject
from ..util import MISSING

if TYPE_CHECKING:
    from typing import Self

    from .channel import MessageableChannel
    from .guild import Guild
    from .member import Member
    from .user import User
    from ..connection import Connection
    from ..types.message import Message as RawMessage

__all__ = ('PartialMessage', 'Message')


class PartialMessage(AdaptObject):
    """Represents a message in Adapt that only operates with a channel, message ID, and potentially a revision ID.

    This is useful for performing operations on messages without having to fetch them first.

    Attributes
    ----------
    channel: :class:`.TextChannel` | :class:`.PrivateChannel` | :class:`.PartialMessageable`
        The channel that the message belongs to.
    """

    __slots__ = ('channel', '_revision_id')

    def __init__(self, *, channel: MessageableChannel, id: int) -> None:
        self.channel = channel
        self._id = id

    def _update(self, data: RawMessage) -> None:
        self._id = data['id']

    @property
    def _connection(self) -> Connection:
        return self.channel._connection

    async def edit(
        self,
        *,
        content: str | None = MISSING,
        embed: Embed | None = MISSING,
        embeds: list[Embed] = MISSING,
    ) -> Self:
        """|coro|

        Edits the message.

        Parameters
        ----------
        content: :class:`str`
            The new content of the message.
        embed: :class:`.Embed` | None
            The new singular embed of the message. This will replace all existing embeds. Must be mutually exclusive
            with the ``embeds`` parameter. If ``None``, all embeds will be removed.
        embeds: list[:class:`.Embed`]
            The new embeds of the message. This will replace all existing embeds. Must be mutually exclusive with the
            ``embed`` parameter. If an empty list is provided, all embeds will be removed.

        Returns
        -------
        :class:`.Message`
            The edited message.
        """
        if embed is not MISSING and embeds is not MISSING:
            raise TypeError('embed and embeds are mutually exclusive parameters')
        if embed is not MISSING:
            embeds = [] if embed is None else [embed]
        if embeds is not MISSING:
            embeds = [embed.to_dict() for embed in embeds]

        self._update(await self._connection.http.edit_message(self.channel.id, self.id, content=content, embeds=embeds))
        return self

    async def delete(self) -> None:
        """|coro|

        Deletes the message.
        """
        await self._connection.http.delete_message(self.channel.id, self.id)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} channel_id={self.channel.id}>'


class Message(PartialMessage):
    """Represents a message in Adapt.

    Attributes
    ----------
    content: :class:`str`
        The content of the message. If no content exists, an empty string is returned.
    embeds: list[:class:`.Embed`]
        The embeds included in this message.
    type: :class:`.MessageType`
        The type of the message.
    flags: :class:`.MessageFlags`
        Special properties about the message.
    """

    __slots__ = (
        'content',
        'embeds',
        '_author',
        'type',
        'flags',
    )

    def __init__(self, *, channel: MessageableChannel, data: RawMessage) -> None:
        super().__init__(channel=channel, id=0)  # ID is set in _update
        self._update(data)

    def _update(self, data: RawMessage) -> None:
        self.content = data['content'] or ''
        self.embeds = [Embed.from_dict(embed) for embed in data['embeds']]

        if author := data['author']:
            # Try upgrading the author to a member if possible
            if (guild_id := author.get('guild_id')) and (guild := self._connection.get_guild(guild_id)):
                self._author = guild._add_raw_member(author)
            else:
                self._author = self._connection.add_raw_user(author)
        else:
            self._author = data['author_id']

        self.type = MessageType(data['type'])
        self.flags = MessageFlags(data['flags'])

        super()._update(data)

    @property
    def author(self) -> User | Member | None:
        """:class:`.User` | :class:`.Member` | None: The author of the message.

        If an author is not applicable, or resolved author data was not provided and the author is not cached,
        this will be ``None``.

        Otherwise, if the message was sent in a guild, this will be a :class:`.Member`. If it was sent in a private
        channel, this will be a :class:`.User`.
        """
        if self._author is None:
            return None
        elif isinstance(self._author, int):
            return self._connection.get_user(self._author)
        return self._author

    @property
    def guild(self) -> Guild | None:
        """:class:`.Guild` | None: The guild that the message was sent in, if applicable."""
        return self.channel.guild

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} channel_id={self.channel.id} author_id={self.author.id}>'
