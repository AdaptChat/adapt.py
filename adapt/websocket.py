from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

from aiohttp import WSMsgType

from .server import AdaptServer

if TYPE_CHECKING:
    from asyncio import Task
    from typing import Any, Callable, TypedDict, TypeAlias, Final, Self

    from aiohttp import ClientSession, ClientWebSocketResponse

    from .connection import Connection
    from .http import HTTPClient
    from .types.ws import InboundMessage

    Dispatcher: TypeAlias = Callable[..., Task[list[Any]]]

try:
    import msgpack
except ModuleNotFoundError:
    HAS_MSGPACK = False
else:
    HAS_MSGPACK = True

DEFAULT_WS_URL: Final[str] = AdaptServer.production().harmony


class AttemptReconnect(Exception):
    pass


class WebSocket:
    """The WebSocket client used to interact with Adapt's websocket, harmony."""

    ws: ClientWebSocketResponse

    def __init__(
        self,
        connection: Connection,
        *,
        loop: asyncio.AbstractEventLoop,
        session: ClientSession,
        dispatch: Dispatcher,
        token: str,
        prefer_msgpack: bool = True,
        ws_url: str = DEFAULT_WS_URL,
    ) -> None:
        self._connection = connection
        self._loop = loop
        self._session = session
        self._dispatch = dispatch
        self._token = token
        self._msgpack = prefer_msgpack and HAS_MSGPACK
        self.ws_url = ws_url

    @classmethod
    def from_http(
        cls,
        connection: Connection,
        http: HTTPClient,
        *,
        dispatch: Dispatcher,
        prefer_msgpack: bool = True,
        ws_url: str = DEFAULT_WS_URL,
    ) -> Self:
        return cls(
            connection,
            loop=http.loop,
            session=http.session,
            dispatch=dispatch,
            token=http.token,
            prefer_msgpack=prefer_msgpack,
            ws_url=ws_url,
        )

    async def send(self, data: dict[Any, Any] | TypedDict) -> None:
        if self._msgpack:
            r = msgpack.packb(data)
            await self.ws.send_bytes(r)
        else:
            r = json.dumps(data)
            await self.ws.send_str(r)
    
    async def process_message(self, data: str | bytes) -> None:
        if self._msgpack and type(data) is bytes:
            msg: InboundMessage = msgpack.unpackb(data)
        else:
            msg: InboundMessage = json.loads(data)

        assert isinstance(msg, dict) and 'event' in msg, 'Received invalid message from websocket'

        event = msg['event']
        args = ()
        if data := msg.get('data'):
            args = (data,)
        self._dispatch('raw_' + event, *args)
        self._connection.process_event(msg)

    async def poll(self) -> None:
        msg = await self.ws.receive()

        if msg.type is WSMsgType.BINARY or msg.type is WSMsgType.TEXT:
            await self.process_message(msg.data)
        elif msg.type is WSMsgType.ERROR:
            raise msg.data
        else:
            raise AttemptReconnect
    
    async def connect(self) -> None:
        self.ws = await self._session.ws_connect(self.ws_url)

        await self.poll()
        await self.send({
            "op": "identify",
            "token": self._token,
            "device": "desktop"
        })
        await self._dispatch("connect")
    
    async def start(self) -> None:
        await self.connect()

        while True:
            try:
                await self.poll()
            except AttemptReconnect:
                await self.connect()
                continue
            except Exception:
                if not self.ws.closed:
                    await self.ws.close()
                raise
