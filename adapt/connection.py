from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from .models.enums import RelationshipType, Status
from .models.ready import ReadyEvent
from .models.user import ClientUser, Relationship, User
from .server import AdaptServer

if TYPE_CHECKING:
    from typing import Any

    from .http import HTTPClient
    from .types.user import User as RawUser, Relationship as RawRelationship
    from .types.ws import InboundMessage, ReadyEvent as RawReadyEvent
    from .websocket import Dispatcher

__all__ = ('Connection',)


class Connection:
    """Represents a connection state to the Adapt API."""

    __slots__ = (
        'http',
        'server',
        'loop',
        'user',
        'dispatch',
        '_connect_status',
        '_is_ready',
        '_token',
        '_max_message_count',
        '_users',
        '_relationships',
        '_channels',
        '_guilds',
    )

    if TYPE_CHECKING:
        _users: dict[int, User]
        _relationships: dict[int, Relationship]
        _channels: dict[int, Any]  # TODO Channel type
        _guilds: dict[int, Any]  # TODO Guild type

    def __init__(
        self,
        *,
        http: HTTPClient,
        server: AdaptServer = AdaptServer.production(),
        loop: asyncio.AbstractEventLoop | None = None,
        dispatch: Dispatcher,
        max_message_count: int = 1000,
        status: Status = Status.online,
    ) -> None:
        self.http = http
        self.server = server
        self.loop = loop or http.loop
        self.user: ClientUser | None = None
        self.dispatch = dispatch

        self._connect_status: Status = status
        self._is_ready: asyncio.Future[ReadyEvent] = loop.create_future()
        self._token: str | None = None
        self._max_message_count = max_message_count

        self._users = {}
        self._relationships = {}
        self._channels = {}
        self._guilds = {}

    def invalidate_caches(self) -> None:
        """Clears the internal caches of the connection."""
        self._users.clear()
        self._relationships.clear()
        self._channels.clear()
        self._guilds.clear()

    def get_user(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    def add_user(self, user: User) -> User:
        self._users[user.id] = user
        return user

    def add_raw_user(self, data: RawUser) -> User:
        if user := self.get_user(data['id']):
            user._update(data)
            return user

        return self.add_user(User(connection=self, data=data))

    def get_relationship(self, user_id: int) -> Relationship | None:
        return self._relationships.get(user_id)

    def update_relationship(self, *, user_id: int, type: RelationshipType) -> Relationship:
        if relationship := self.get_relationship(user_id):
            relationship._type = type
            return relationship

        self._relationships[user_id] = new = Relationship(connection=self, user_id=user_id, type=type)
        return new

    def update_raw_relationship(self, data: RawRelationship) -> Relationship:
        self.add_raw_user(user := data['user'])
        return self.update_relationship(user_id=user['id'], type=RelationshipType(data['type']))

    def process_event(self, data: InboundMessage) -> None:
        event: str = data['event']
        data: dict[str, Any] = data.get('data')

        if handler := getattr(self, '_handle_' + event, None):
            handler(data)

    def _handle_ready(self, data: RawReadyEvent) -> None:
        ready = ReadyEvent(connection=self, data=data)

        if not self._is_ready.done():
            self._is_ready.set_result(ready)

        self.dispatch('ready', ready)
