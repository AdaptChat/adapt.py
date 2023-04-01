from __future__ import annotations

from typing import TYPE_CHECKING

from .user import ClientUser

if TYPE_CHECKING:
    from ..connection import Connection
    from ..types.ws import ReadyEvent as RawReadyEvent

__all__ = ('ReadyEvent',)


class ReadyEvent:
    """Represents the ready event from the gateway. This event is sent when the client is ready to receive events.

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

    # TODO:
    guilds: list[Guild]
    dm_channels: list[DMChannel]
    presences: list[Presence]
    relationships: list[Relationship]

    def __init__(self, *, connection: Connection, data: RawReadyEvent) -> None:
        self._connection = connection
        self.session_id = data['session_id']
        self.user = ClientUser(connection=connection, data=data['user'])

    def __repr__(self) -> str:
        return f'<ReadyEvent session_id={self.session_id!r} user={self.user!r}>'