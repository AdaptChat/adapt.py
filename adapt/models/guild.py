from __future__ import annotations

from typing import TYPE_CHECKING

from .asset import Asset
from .bitflags import GuildFlags
from .channel import TextChannel, _guild_channel_factory
from .object import AdaptObject
from ..util import MISSING

if TYPE_CHECKING:
    from typing import Generator, ValuesView, Self

    from .channel import GuildChannel
    from .member import Member, PartialMember
    from .object import ObjectLike
    from ..connection import Connection
    from ..types.channel import GuildChannel as RawGuildChannel
    from ..types.guild import PartialGuild as RawPartialGuild, Guild as RawGuild, Member as RawMember
    from ..util import IOSource

__all__ = ('PartialGuild', 'Guild')


class PartialGuild(AdaptObject):
    """A partial guild object which operates with only an ID.

    This is useful for performing operations on guilds without having to fetch them first.

    .. note::
        Unlike a full :class:`.Guild`, partial guilds will not perform any permission checks locally and will instead
        rely on the API to perform them. This could result in more unnecessary API calls being made.

    .. note::
        This is not to be confused with the official ``PartialGuild`` model in the Adapt API protocol, which is a
        guild without member, channel, and role data. This is a guild object that only operates with an ID.
    """

    __slots__ = ('_connection',)

    def __init__(self, *, connection: Connection, id: int) -> None:
        self._id = id
        self._connection = connection

    def _update(self, data: dict) -> None:
        if id := data.get('id'):
            self._id = id

    def get_partial_member(self, member_id: int) -> PartialMember:
        """Creates a usable partial member object that operates with only its ID.

        This is useful for when you want to perform actions on a member without having to ensure it is cached
        or fetch unnecessary guild or member data.

        Parameters
        ----------
        member_id: :class:`int`
            The user ID to create the partial member with.

        Returns
        -------
        :class:`.PartialMember`
            The partial member object that was created.
        """
        from .member import PartialMember

        return PartialMember(guild=self, id=member_id)

    async def _perform_edit(self, **kwargs) -> RawPartialGuild:
        return await self._connection.http.edit_guild(self.id, **kwargs)

    async def edit(
        self,
        *,
        name: str = MISSING,
        description: str | None = MISSING,
        icon: IOSource | None = MISSING,
        banner: IOSource | None = MISSING,
        public: bool = MISSING,
    ) -> None:
        """|coro|

        Edits the properties for the guild. Only the parameters passed will be updated.

        .. note::
            Nothing is returned from this method. If you wish to get the updated guild object, perform the edit on a
            full :class:`.Guild` object instead.

        Parameters
        ----------
        name: :class:`str`
            The new name for the guild.
        description: :class:`str`
            The new description for the guild. Set to ``None`` to remove the description.
        icon: :class:`bytes`, path-like object, file-like object, or ``None``
            The new icon for the guild. Set to ``None`` to remove the icon.
        banner: :class:`bytes`, path-like object, file-like object, or ``None``
            The new banner for the guild. Set to ``None`` to remove the banner.
        public: :class:`bool`
            Whether the guild is public or not.
        """
        await self._perform_edit(
            name=name, description=description, icon=icon, banner=banner, public=public,
        )

    async def delete(self, *, password: str = MISSING) -> None:
        """|coro|

        Deletes the guild.

        Parameters
        ----------
        password: :class:`str`
            Your account password. This **must** be specified when deleting user accounts for security purposes.
            This should not be specified when deleting bot accounts.
        """
        await self._connection.http.delete_guild(self.id, password=password)

    async def leave(self) -> None:
        """|coro|

        Leaves the guild.
        """
        await self._connection.http.leave_guild(self.id)

    async def kick(self, member: ObjectLike) -> None:
        """|coro|

        Kicks the member from the guild. You must have the :attr:`.Permissions.kick_members` permission to do this.

        Parameters
        ----------
        member: :class:`.Member`-like
            The member to kick.
        """
        await self._connection.http.kick_member(self.id, member.id)

    def __repr__(self) -> str:
        return f'<PartialGuild id={self.id}>'


class _GuildCacheIntegrity:
    __slots__ = ('_members', '_roles', '_channels')

    def __init__(self) -> None:
        self._members: bool = False
        self._roles: bool = False
        self._channels: bool = False

    @property
    def members(self) -> bool:
        """:class:`bool`: Whether the guild's members are cached."""
        return self._members

    @property
    def roles(self) -> bool:
        """:class:`bool`: Whether the guild's roles are cached."""
        return self._roles

    @property
    def channels(self) -> bool:
        """:class:`bool`: Whether the guild's channels are cached."""
        return self._channels


class Guild(PartialGuild):
    """Represents a guild in Adapt.

    Attributes
    ----------
    name: :class:`str`
        The name of the guild.
    description: :class:`str` | None
        The description of the guild.
    owner_id: :class:`int`
        The ID of the user that owns the guild.
    vanity_code: :class:`str` | None
        The vanity URL code of the guild. This solely includes the code, not the full URL.
        This is ``None`` if the guild does not have a vanity URL.
    """

    __slots__ = (
        'name',
        'description',
        '_icon',
        '_banner',
        'owner_id',
        '_flags',
        'vanity_code',
        '_members',
        '_roles',
        '_channels',
        '_integrity',
    )

    def __init__(self, *, connection: Connection, data: RawPartialGuild | RawGuild) -> None:
        self._members: dict[int, Member] = {}
        self._roles: dict[int, Role] = {}
        self._channels: dict[int, GuildChannel] = {}
        self._integrity = _GuildCacheIntegrity()

        super().__init__(connection=connection, id=data['id'])
        self._update(data)

    def _update(self, data: RawPartialGuild | RawGuild) -> None:
        super()._update(data)
        self.name = data['name']
        self.description = data['description']
        self._icon = data['icon']
        self._banner = data['banner']
        self.owner_id = data['owner_id']
        self._flags = data['flags']
        self.vanity_code = data['vanity_url']

        if members := data.get('members'):
            for member in members:
                self._add_raw_member(member)
            self._integrity._members = True

        if channels := data.get('channels'):
            for channel in channels:
                self._add_raw_channel(channel)
            self._integrity._channels = True

    def _add_member(self, member: Member) -> Member:
        self._members[member.id] = member
        return member

    def _add_raw_member(self, data: RawMember) -> Member:
        from .member import Member

        if member := self._members.get(data['id']):
            member._update(data)
            return member

        member = Member(guild=self, data=data)
        self._connection.add_raw_user(data)
        return self._add_member(member)

    def _add_channel(self, channel: GuildChannel) -> GuildChannel:
        self._channels[channel.id] = channel
        return channel

    def _add_raw_channel(self, data: RawGuildChannel) -> GuildChannel:
        if channel := self._channels.get(data['id']):
            channel._update(data)
            return channel

        channel = _guild_channel_factory(guild=self, data=data)
        return self._add_channel(channel)

    @property
    def members(self) -> ValuesView[Member]:
        """Iterable[:class:`.Member`]: An iterable of the guild's members."""
        return self._members.values()

    def get_member(self, member_id: int) -> Member | None:
        """Returns the member with the given ID, resolved from the cache.

        Parameters
        ----------
        member_id: :class:`int`
            The ID of the member to get.

        Returns
        -------
        :class:`.Member` | None
            The member with the given ID, or ``None`` if not found in the cache.
        """
        return self._members.get(member_id)

    async def fetch_member(self, member_id: int, *, respect_cache: bool = True) -> Member:
        """|coro|

        Fetches the member with the given ID from the API.

        Parameters
        ----------
        member_id: :class:`int`
            The ID of the member to fetch.
        respect_cache: :class:`bool`
            Whether to respect the cache or not. If ``True``, the cache will be checked first.

        Returns
        -------
        :class:`.Member`
            The member with the given ID.
        """
        if member := respect_cache and self.get_member(member_id):
            return member

        data = await self._connection.http.get_member(self.id, member_id)
        return self._add_raw_member(data)

    @property
    def channels(self) -> ValuesView[GuildChannel]:
        """Iterable[:class:`.GuildChannel`]: An iterable of the guild's channels."""
        return self._channels.values()

    @property
    def text_channels(self) -> Generator[TextChannel, None, None]:
        """Iteratable[:class:`.TextBasedGuildChannel`]: An iterator of the guild's text-based channels."""
        return (channel for channel in self.channels if isinstance(channel, TextChannel))

    def get_channel(self, channel_id: int) -> GuildChannel | None:
        """Returns the channel with the given ID, resolved from the cache.

        Parameters
        ----------
        channel_id: :class:`int`
            The ID of the channel to get.

        Returns
        -------
        :class:`.GuildChannel` | None
            The channel with the given ID, or ``None`` if not found in the cache.
        """
        return self._channels.get(channel_id)

    async def fetch_channel(self, channel_id: int, *, respect_cache: bool = True) -> GuildChannel:
        """|coro|

        Fetches the channel with the given ID from the API.

        Parameters
        ----------
        channel_id: :class:`int`
            The ID of the channel to fetch.
        respect_cache: :class:`bool`
            Whether to respect the cache or not. If ``True``, the cache will be checked first.

        Returns
        -------
        :class:`.GuildChannel`
            The channel with the given ID.
        """
        if channel := respect_cache and self.get_channel(channel_id):
            return channel

        data = await self._connection.http.get_channel(channel_id)
        return self._add_raw_channel(data)

    @property
    def cache_integrity(self) -> _GuildCacheIntegrity:
        """Returns the integrity of the guild's cache.

        This is a :class:`.NamedTuple` with the following boolean attributes:

        - ``members``: Whether the guild's members are cached.
        - ``roles``: Whether the guild's roles are cached.
        - ``channels``: Whether the guild's channels are cached.
        """
        return self._integrity

    @property
    def me(self) -> Member | None:
        """:class:`.Member`: The member that represents the client in the guild, if available in cache.

        This is equivalent to ``guild.get_member(client.user.id)``.
        """
        return self.get_member(self._connection.user.id)

    @property
    def icon(self) -> Asset:
        """:class:`.Asset`: The guild's icon."""
        return Asset(connection=self._connection, url=self._icon)

    @property
    def banner(self) -> Asset:
        """:class:`.Asset`: The guild's banner."""
        return Asset(connection=self._connection, url=self._banner)

    @property
    def flags(self) -> GuildFlags:
        """:class:`.GuildFlags`: Special properties and features about the guild."""
        return GuildFlags(self._flags)

    @property
    def public(self) -> bool:
        """:class:`bool`: Whether the guild is public."""
        return self.flags.public

    @property
    def verified(self) -> bool:
        """:class:`bool`: Whether the guild is verified."""
        return self.flags.verified

    @property
    def owner(self) -> Member | None:
        """:class:`.Member` | None: The resolved member object of the guild owner, if available in cache."""
        return self.get_member(self.owner_id)

    async def edit(
        self,
        *,
        name: str = MISSING,
        description: str | None = MISSING,
        icon: IOSource | None = MISSING,
        banner: IOSource | None = MISSING,
        public: bool = MISSING,
    ) -> Self:
        """|coro|

        Edits the properties for the guild. Only the parameters passed will be updated.

        Parameters
        ----------
        name: :class:`str`
            The new name for the guild.
        description: :class:`str`
            The new description for the guild. Set to ``None`` to remove the description.
        icon: :class:`bytes`, path-like object, file-like object, or ``None``
            The new icon for the guild. Set to ``None`` to remove the icon.
        banner: :class:`bytes`, path-like object, file-like object, or ``None``
            The new banner for the guild. Set to ``None`` to remove the banner.
        public: :class:`bool`
            Whether the guild is public or not.

        Returns
        -------
        :class:`.Guild`
            The updated guild object.
        """
        self._update(await self._perform_edit(
            name=name, description=description, icon=icon, banner=banner, public=public,
        ))
        return self

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<Guild id={self.id} name={self.name!r}>'
