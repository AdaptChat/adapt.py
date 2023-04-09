from __future__ import annotations

from typing import cast, NamedTuple, TYPE_CHECKING

from .asset import Asset
from .bitflags import GuildFlags
from .object import AdaptObject
from ..util import MISSING

if TYPE_CHECKING:
    from typing import Self

    from ..connection import Connection
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

    def __repr__(self) -> str:
        return f'<PartialGuild id={self.id}>'


class _GuildIntegrity:
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
        self._integrity: _GuildIntegrity = _GuildIntegrity()

        super().__init__(connection=connection, id=data['id'])
        self._update(cast('RawGuild', data))

    def _update(self, data: RawGuild) -> None:
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

    def _add_member(self, member: Member) -> Member:
        self._members[member.id] = member
        return member

    def _add_raw_member(self, data: RawMember) -> Member:
        if member := self._members.get(data['id']):
            member._update(data)
            return member

        member = ...  # TODO
        return self._add_member(member)

    @property
    def cache_integrity(self) -> _GuildIntegrity:
        """Returns the integrity of the guild's cache.

        This is a :class:`.NamedTuple` with the following boolean attributes:

        - ``members``: Whether the guild's members are cached.
        - ``roles``: Whether the guild's roles are cached.
        - ``channels``: Whether the guild's channels are cached.
        """
        return self._integrity

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
        return self._members.get(self.owner_id)

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
        self._update(cast('RawGuild', await self._perform_edit(
            name=name, description=description, icon=icon, banner=banner, public=public,
        )))
        return self

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<Guild id={self.id} name={self.name!r}>'
