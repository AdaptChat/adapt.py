from __future__ import annotations

from typing import TYPE_CHECKING

from .guild import Guild, PartialGuild
from .user import PartialUser, User
from ..util import parse_datetime

if TYPE_CHECKING:
    from datetime import datetime

    from ..connection import Connection
    from ..types.guild import Member as RawMember

__all__ = ('PartialMember', 'Member')


class PartialMemberMixin:
    __slots__ = ()

    if TYPE_CHECKING:
        _connection: Connection
        guild: PartialGuild

        @property
        def id(self) -> int:
            ...

    @property
    def is_me(self) -> bool:
        """Whether this member is the client user."""
        return self.id == self._connection.user.id

    async def kick(self) -> None:
        """|coro|

        Kicks the member from the guild. You must have the :attr:`.Permissions.kick_members` permission to do this.
        This is a shortcut for calling :meth:`.Guild.kick` with this member.
        """
        await self._connection.http.kick_member(self.guild.id, self.id)


class PartialMember(PartialUser, PartialMemberMixin):
    """Represents a partial member of a guild.

    This is useful for performing operations on members without having to fetch them first.

    Attributes
    ----------
    guild: :class:`.PartialGuild`
        The guild that the member is in. This *may* be a partial guild.
    """

    __slots__ = ('guild',)

    if TYPE_CHECKING:
        guild: PartialGuild

    def __init__(self, *, guild: PartialGuild, id: int) -> None:
        super().__init__(connection=guild._connection, id=id)
        self.guild = guild

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} guild_id={self.guild.id}>'


class Member(User, PartialMemberMixin):
    """Represents a member of a guild."""

    __slots__ = (
        'guild',
        'nick',
        '_roles',
        'joined_at',
    )

    if TYPE_CHECKING:
        guild: Guild
        nick: str | None
        _roles: set[int]
        joined_at: datetime

    def __init__(self, *, guild: Guild, data: RawMember) -> None:
        super().__init__(connection=guild._connection, data=data)
        self.guild: Guild = guild

    def _update(self, data: RawMember) -> None:
        super()._update(data)
        self.nick = data['nick']
        self.joined_at = parse_datetime(data['joined_at'])

        roles = data['roles']
        if roles is not None:
            self._roles = set(roles)

    @property
    def user(self) -> User:
        """:class:`User`: The user that this member represents.

        Although members are a subclass of users, this property is provided for completeness.
        """
        return self._connection.get_user(self.id) or self

    @property
    def display_name(self) -> str:
        """:class:`str`: The member's display name.

        This is their nickname if they have one, otherwise it is their username.
        """
        return self.nick or self.username

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} guild_id={self.guild.id}>'
