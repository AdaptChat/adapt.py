from __future__ import annotations

from typing import NamedTuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..types.ws import ReadyEvent as RawReadyEvent


class ReadyEvent(NamedTuple):
    """Represents the ready event from the gateway. This event is sent when the client is ready to receive events.

    .. note::
        Like partial models, this model is stateless and is immutable. It is internally represented as a tuple.

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
    session_id: str
    user: ClientUser
    guilds: list[Guild]
    dm_channels: list[DMChannel]
    presences: list[Presence]
    relationships: list[Relationship]

    @classmethod
    def from_raw(cls, raw: RawReadyEvent) -> ReadyEvent:
        """Creates a :class:`.ReadyEvent` from a raw event."""
        return cls(
            session_id=raw['session_id'],
            user=ClientUser.from_raw(raw['user']),
            guilds=[Guild.from_raw(g) for g in raw['guilds']],
            dm_channels=[DMChannel.from_raw(c) for c in raw['dm_channels']],
            presences=[Presence.from_raw(p) for p in raw['presences']],
            relationships=[Relationship.from_raw(r) for r in raw['relationships']],
        )

    def __repr__(self) -> str:
        return f'<ReadyEvent session_id={self.session_id!r} user={self.user!r}>'
