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
    'Permissions',
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

    Bitflags are a way to represent multiple boolean values in a single integer. This class provides a way to easily
    read and manipulate these boolean values.

    Parameters
    ----------
    value: :class:`int`
        The initial bits. If not provided, the default value will be used (typically ``0`` unless specified).
    **flags: :class:`bool`
        The overrides for each flag. If a flag is not provided, it will be set to ``False``.

    Attributes
    ----------
    value: :class:`int`
        The current bits.

    Examples
    --------
    We will use the :class:`Permissions` class as an example.

    Create a new permissions instance with specific flags: ::

        permissions = Permissions(view_channel=True, send_messages=True)

    Create a new permissions instance with a specific value: ::

        permissions = Permissions(5)  # Equivalent to Permissions(view_channel=True, send_messages=True)

    Read the value of a specific flag: ::

        permissions.view_channel  # True
        permissions.add_reactions  # False

    Set the value of a specific flag: ::

        permissions.view_channel = False
        permissions.view_channel  # False

        # Using the `del` keyword will set the flag to False
        del permissions.view_channel  # Equivalent to permissions.view_channel = False

    Create a new permissions instance from another: ::

        permissions = Permissions(view_channel=True, send_messages=True)
        modified = permissions.copy_with(send_messages=False)

        permissions.send_messages  # True
        modified.send_messages  # False

    Helper methods are also provided to make it easier to work with bitflags: ::

        no_permissions = Permissions.none()  # Equivalent to Permissions(0)
        all_permissions = Permissions.all()  # Enable all flags
        default_permissions = Permissions.default()  # Use the default value

    Turn a permissions instance into a dictionary: ::

        permissions = Permissions(view_channel=True, send_messages=True)
        dict(permissions)  # {'view_channel': True, 'send_messages': True, 'add_reactions': False, ...}

        # Turn it into a list of enabled flags
        [name for name, value in permissions if value]  # ['view_channel', 'send_messages']
    """

    value: int

    __valid_flags__: ClassVar[dict[str, int]]
    __default_value__: ClassVar[int] = 0
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

    @classmethod
    def default(cls) -> Self:
        """Creates a new instance with the default flags.

        Returns
        -------
        :class:`Bitflags`
            The new instance.
        """
        return cls(cls.__default_value__)

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
    default_role: :class:`bool`
        Whether the role is the default role for everyone.
    """
    hoisted = _(1 << 0)
    managed = _(1 << 1)
    mentionable = _(1 << 2)
    default_role = _(1 << 3)


class Permissions(Bitflags):
    """|bitflags|

    Represents a set of permissions.

    Attributes
    ----------
    view_channel: :class:`bool`
        People with this permission can view channels and receive events from them.
    view_message_history: :class:`bool`
        People with this permission can view the message history of channels. The
        `view_channel` permission is not necessarily required to view the message history,
        however it means you cannot receive or send new messages in the channel.
    send_messages: :class:`bool`
        People with this permission can send messages in channels. The `view_channel`
        permission *is* required to send messages.
    manage_messages: :class:`bool`
        People with this permission can manage messages sent by other people. This allows
        for the following:

        * Deleting messages sent by others
        * Deleting attachments or embeds sent by others
        * Removing reactions of others
        * Unpublishing messages sent by others (Announcement channels only)

        Note that anyone can still delete their own messages.
    attach_files: :class:`bool`
        People with this permission can attach files to messages.
    send_embeds: :class:`bool`
        People with this permission can send rich embeds or have embed links automatically
        appear.
    add_reactions: :class:`bool`
        People with this permission can add new reactions to messages. Note that users
        without this permission can still react to already existing reactions.
    pin_messages: :class:`bool`
        People with this permission can pin *and* unpin messages.
    star_messages: :class:`bool`
        People with this permission can star and unstar messages.
    publish_messages: :class:`bool`
        People with this permission can publish messages to the announcement feed.
    modify_channels: :class:`bool`
        People with this permission can manage settings of channels.
    manage_channels: :class:`bool`
        People with this permission can manage channels.
    manage_webhooks: :class:`bool`
        People with this permission can create, edit, and delete webhooks.
    manage_emojis: :class:`bool`
        People with this permission can create, edit, and delete emojis.
    manage_starboard: :class:`bool`
        People with this permission can delete starboard posts, or disable the starboard completely.
    manage_guild: :class:`bool`
        People with this permission can manage the guild's settings.
    manage_roles: :class:`bool`
        People with this permission can manage the guild's roles. They will be able to
        change the permissions of any roles below their top role, and they will be forbidden to
        grant or deny any permissions they do not have themselves. They can also assign and
        remove any roles to other members, as long as the target role is below their top role.
    create_invites: :class:`bool`
        People with this permission can create invites to the guild.
    manage_invites: :class:`bool`
        People with this permission can revoke or pause invites of any channel in the guild.
        This does not take into account the `create_invites` permission, meaning they can revoke
        invites even if they cannot create them.
    use_external_emojis: :class:`bool`
        People with this permission can use emojis found in other servers.
    change_nickname: :class:`bool`
        People with this permission can change their own nickname.
    manage_nicknames: :class:`bool`
        People with this permission can change the nickname of other people.
    timeout_members: :class:`bool`
        People with this permission can timeout and untimeout members that are lower than
        them in role hierarchy.
    kick_members: :class:`bool`
        People with this permission can kick members that are lower than them in role
        hierarchy.
    ban_members: :class:`bool`
        People with this permission can ban and unban members that are lower than them in
        role hierarchy.
    bulk_delete_messages: :class:`bool`
        People with this permission can delete or purge messages in bulk.
        Unlike Discord, the API allows for up to any number of messages to be deleted at a time.
    view_audit_log: :class:`bool`
        People with this permission can view an audit log of past moderation or other
        privileged actions.
    privileged_mentions: :class:`bool`
        People with this permission can mention large groups of people. This means
        mentioning everyone under a non-mentionable role or mentioning everyone.
    connect: :class:`bool`
        People with this permission can connect to a voice channel.
    speak: :class:`bool`
        People with this permission can speak in a voice channel.
    mute_members: :class:`bool`
        People with this permission can mute other members in a voice channel.
    deafen_members: :class:`bool`
        People with this permission can deafen other members in a voice channel.
    administrator: :class:`bool`
        People with this permission have the ability to override all permissions and any
        channel. This means that despite any overwrites, they will have all permissions
        throughout the entire guild.
    """
    view_channel = _(1 << 0)
    view_message_history = _(1 << 1)
    send_messages = _(1 << 2)
    manage_messages = _(1 << 3)
    attach_files = _(1 << 4)
    send_embeds = _(1 << 5)
    add_reactions = _(1 << 6)
    pin_messages = _(1 << 7)
    star_messages = _(1 << 8)
    publish_messages = _(1 << 9)
    modify_channels = _(1 << 10)
    manage_channels = _(1 << 11)
    manage_webhooks = _(1 << 12)
    manage_emojis = _(1 << 13)
    manage_starboard = _(1 << 14)
    manage_guild = _(1 << 15)
    manage_roles = _(1 << 16)
    create_invites = _(1 << 17)
    manage_invites = _(1 << 18)
    use_external_emojis = _(1 << 19)
    change_nickname = _(1 << 20)
    manage_nicknames = _(1 << 21)
    timeout_members = _(1 << 22)
    kick_members = _(1 << 23)
    ban_members = _(1 << 24)
    bulk_delete_messages = _(1 << 25)
    view_audit_log = _(1 << 26)
    privileged_mentions = _(1 << 27)
    connect = _(1 << 28)
    speak = _(1 << 29)
    mute_members = _(1 << 30)
    deafen_members = _(1 << 31)
    administrator = _(1 << 32)

    __default_value__ = (
        view_channel
        | view_message_history
        | send_messages
        | add_reactions
        | star_messages
        | attach_files
        | send_embeds
        | create_invites
        | use_external_emojis
        | change_nickname
        | connect
        | speak
    )
