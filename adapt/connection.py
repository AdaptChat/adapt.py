from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from .models.ready import ReadyEvent
from .models.user import ClientUser

if TYPE_CHECKING:
    from typing import Any

    from .types.ws import InboundMessage
    from .websocket import Dispatcher


class Connection:
    """Represents a connection state to the Adapt API."""

    def __init__(
        self,
        *,
        loop: asyncio.AbstractEventLoop,
        dispatch: Dispatcher,
        max_message_count: int = 1000,
    ) -> None:
        self.loop = loop
        self.user: ClientUser | None = None
        self.dispatch = dispatch

        self._is_ready: asyncio.Future = loop.create_future()
        self._token: str | None = None
        self._max_message_count = max_message_count

    def process_event(self, data: InboundMessage) -> None:
        event: str = data['event']
        data: dict[str, Any] = data.get('data')

        if handler := getattr(self, '_handle_' + event, None):
            await handler(data)

    def _handle_ready(self, data: dict[str, Any]) -> None:
        self.user = ClientUser(self, data)
        self._is_ready.set_result(None)

        self.dispatch('ready', ReadyEvent.from_raw(data))
