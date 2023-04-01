from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from .models.ready import ReadyEvent
from .models.user import ClientUser
from .server import AdaptServer

if TYPE_CHECKING:
    from typing import Any

    from .http import HTTPClient
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
        '_is_ready',
        '_token',
        '_max_message_count',
    )

    def __init__(
        self,
        *,
        http: HTTPClient,
        server: AdaptServer = AdaptServer.production(),
        loop: asyncio.AbstractEventLoop | None = None,
        dispatch: Dispatcher,
        max_message_count: int = 1000,
    ) -> None:
        self.http = http
        self.server = server
        self.loop = loop or http.loop
        self.user: ClientUser | None = None
        self.dispatch = dispatch

        self._is_ready: asyncio.Future[ReadyEvent] = loop.create_future()
        self._token: str | None = None
        self._max_message_count = max_message_count

    def process_event(self, data: InboundMessage) -> None:
        event: str = data['event']
        data: dict[str, Any] = data.get('data')

        if handler := getattr(self, '_handle_' + event, None):
            handler(data)

    def _handle_ready(self, data: RawReadyEvent) -> None:
        ready = ReadyEvent(connection=self, data=data)
        self.user = ready.user
        if not self._is_ready.done():
            self._is_ready.set_result(ready)

        self.dispatch('ready', ready)
