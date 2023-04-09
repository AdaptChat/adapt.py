from __future__ import annotations

from typing import TYPE_CHECKING

from .channel import DMChannel
from .enums import RelationshipType
from .guild import Guild
from .user import ClientUser, User, Relationship

if TYPE_CHECKING:
    from ..connection import Connection
    from ..types.ws import ReadyEvent as RawReadyEvent

__all__ = ('ReadyEvent',)


class ReadyEvent:
    """Represents the ready event from the gateway. This event is sent when the client is ready to receive events.

    .. note::
        Just like all models, this class is not meant to be constructed by the user. However, if for some reason you
        need to construct this class, it should be known that the constructor mutates the given connection state, which
        could lead to unexpected behaviour.

    Attributes
    ----------
    session_id: :class:`str`
        The session ID used to identify the current websocket connection.
    user: :class:`.ClientUser`
        The client user object.
    guilds: list[:class:`.Guild`]
        A list of guilds the client is in.
    dm_channels: list[:class:`.DMChannel`]
        A list of DM channels the client is in.
    presences: list[:class:`.Presence`]
        A list of presences the client has.
    relationships: list[:class:`.Relationship`]
        A list of relationships the client has with other users.
    """

    __slots__ = (
        '_connection',
        'session_id',
        'user',
        'guilds',
        'dm_channels',
        'presences',
        'relationships',
    )

    _connection: Connection
    session_id: str
    user: ClientUser
    guilds: list[Guild]
    dm_channels: list[DMChannel]
    relationships: list[Relationship]

    # TODO
    presences: list[Presence]

    def __init__(self, *, connection: Connection, data: RawReadyEvent) -> None:
        self._connection = connection
        self.session_id = data['session_id']

        self.user = connection.user = ClientUser(connection=connection, data=data['user'])
        # Slight optimization to avoid unnecessary updates if users are already cached
        relationships: list[Relationship] = []
        seen: set[int] = set(connection._users)

        for relationship in data['relationships']:
            user_data = relationship['user']
            user_id = user_data['id']

            if user_id not in seen:
                connection.add_user(User(connection=connection, data=user_data))
                seen.add(user_id)

            full = connection.update_relationship(user_id=user_id, type=RelationshipType(relationship['type']))
            relationships.append(full)

        self.relationships = relationships
        self.guilds = [self._connection.add_raw_guild(guild) for guild in data['guilds']]
        self.dm_channels = [self._connection.add_raw_dm_channel(dm) for dm in data['dm_channels']]

    def __repr__(self) -> str:
        return f'<ReadyEvent session_id={self.session_id!r} user={self.user!r}>'
