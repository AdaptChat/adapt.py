from __future__ import annotations

from functools import reduce
from operator import or_
from typing import TYPE_CHECKING, cast

from ..util import MISSING

if TYPE_CHECKING:
    from typing import Any, ClassVar, Iterator, Self

__all__ = (
    'Bitflags',
    'UserFlags',
    'PrivacyConfiguration',
    'GuildFlags',
    'MessageFlags',
    'RoleFlags',
)

_ = lambda value: cast(bool, value)


def _create_property(member: int) -> property:
    def _has(self: Bitflags) -> bool:
        return self.value & member == member

    def _set(self: Bitflags, value: bool):
        if value:
            self.value |= member
        else:
            self.value &= ~member

    def _del(self: Bitflags):
        self.value &= ~member

    return property(_has, _set, _del)


class Bitflags:
    """The base class that all bitflag classes inherit from. This class is not meant to be used directly.

    Bitflags are a way to represent multiple boolean values in a single integer. Examples o
    """

    value: int

    __valid_flags__: ClassVar[dict[str, int]]
    __default_value__: ClassVar[int]
    __all_value__: ClassVar[int]

    __slots__ = ('value',)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        valid_flags = {}

        for base in cls.__mro__:
            for name, member in base.__dict__.items():
                if isinstance(member, int) and not name.startswith('_'):
                    valid_flags[name] = member
                    setattr(cls, name, _create_property(member))

        cls.__valid_flags__ = valid_flags
        cls.__default_value__ = kwargs.pop('default', 0)
        cls.__all_value__ = reduce(or_, valid_flags.values())

    def __init__(self, value: int = MISSING, **flags: bool):
        self.value = value or self.__default_value__

        for name, value in flags.items():
            try:
                setattr(self, name, value)
            except AttributeError:
                raise ValueError(f'Invalid flag: {name}')

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} value={self.value}>'

    def __iter__(self) -> Iterator[tuple[str, bool]]:
        for name in self.__valid_flags__:
            yield name, getattr(self, name)

    def __bool__(self) -> bool:
        return bool(self.value)

    def __or__(self, other: Self) -> Self:
        return self.__class__(self.value | other.value)

    def __and__(self, other: Self) -> Self:
        return self.__class__(self.value & other.value)

    def __xor__(self, other: Self) -> Self:
        return self.__class__(self.value ^ other.value)

    def __invert__(self) -> Self:
        return self.__class__(self.__all_value__ ^ self.value)

    def __ior__(self, other: Self) -> Self:
        self.value |= other.value
        return self

    def __iand__(self, other: Self) -> Self:
        self.value &= other.value
        return self

    def __ixor__(self, other: Self) -> Self:
        self.value ^= other.value
        return self

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.value == other.value

    def __ne__(self, other: Any) -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash(self.value)

    @classmethod
    def none(cls) -> Self:
        """Creates a new instance with all flags set to ``False``.

        Returns
        -------
        :class:`Bitflags`
            The new instance.
        """
        return cls(0)

    @classmethod
    def all(cls) -> Self:
        """Creates a new instance with all flags set to ``True``.

        Returns
        -------
        :class:`Bitflags`
            The new instance.
        """
        return cls(cls.__all_value__)

    def copy_with(self, **overrides: bool) -> Self:
        """Returns a copy of this instance with the given flag overrides applied.

        Parameters
        ----------
        **overrides: :class:`bool`
            The flags to override.

        Returns
        -------
        :class:`Bitflags`
            The new instance.
        """
        return self.__class__(self.value, **overrides)


class UserFlags(Bitflags):
    """|bitflags|

    Represents special properties about a user.

    Attributes
    ----------
    bot: :class:`bool`
        Whether the user is a bot.
    """
    bot = _(1 << 0)


class PrivacyConfiguration(Bitflags):
    """|bitflags|

    Represents the privacy configuration of a user.

    Attributes
    ----------
    friends: :class:`bool`
        This configuration is public for friends.
    mutual_friends: :class:`bool`
        This configuration is public for mutual friends (friends of friends).
    guild_members: :class:`bool`
        This configuration is public for users who share a guild with you.
    everyone: :class:`bool`
        This configuration is public for everyone. This overrides all other configurations.
    """
    friends = _(1 << 0)
    mutual_friends = _(1 << 1)
    guild_members = _(1 << 2)
    everyone = _(1 << 3)

    # Aliases
    default_dm_privacy = friends | mutual_friends | guild_members
    default_group_dm_privacy = friends
    default_friend_request_privacy = everyone


class GuildFlags(Bitflags):
    """|bitflags|

    Represents extra properties and features about a guild.

    Attributes
    ----------
    public: :class:`bool`
        The guild is a public guild.
    verified: :class:`bool`
        The guild is verified or official guild.
    vanity_url: :class:`bool`
        The guild has a vanity invite URL.
    """
    public = _(1 << 0)
    verified = _(1 << 1)
    vanity_url = _(1 << 2)


class MessageFlags(Bitflags):
    """|bitflags|
    
    Represents extra properties and features about a message.
    
    Attributes
    ----------
    pinned: :class:`bool`
        The message is pinned.
    system: :class:`bool`
        The message is a system message.
    crosspost: :class:`bool`
        The message is a subscribed crosspost from an announcement channel.
    published: :class:`bool`
        This message has been published to subscribed channels in an announcement channel.
    """
    pinned = _(1 << 0)
    system = _(1 << 1)
    crosspost = _(1 << 2)
    published = _(1 << 3)


class RoleFlags(Bitflags):
    """|bitflags|

    Represents extra properties and features about a role.

    Attributes
    ----------
    hoisted: :class:`bool`
         Whether the role is hoisted, or shown separately, in the members list.
    managed: :class:`bool`
        Whether the role is managed. Managed roles cannot be edited or deleted.
    mentionable: :class:`bool`
        Whether the role is mentionable.
    default: :class:`bool`
        Whether the role is the default role for everyone.
    """
    hoisted = _(1 << 0)
    managed = _(1 << 1)
    mentionable = _(1 << 2)
    default = _(1 << 3)
