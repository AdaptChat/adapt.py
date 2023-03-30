from __future__ import annotations

from typing import TYPE_CHECKING
import json

from aiohttp import WSMsgType

if TYPE_CHECKING:
    from asyncio import Task
    from typing import Any, Callable, TypedDict, TypeAlias, Final

    from aiohttp import ClientSession, ClientWebSocketResponse

    from .types.ws import InboundMessage

    Dispatcher: TypeAlias = Callable[..., Task[list[Any]]]

try:
    import msgpack
except ModuleNotFoundError:
    HAS_MSGPACK = False
else:
    HAS_MSGPACK = True

DEFAULT_WS_URL: Final[str] = "wss://harmony.adapt.chat"


class AttemptReconnect(Exception):
    ...

class WebSocket:
    """The WebSocket client used to interact with Adapt Websocket server"""

    def __init__(self, session: ClientSession, dispatch: Dispatcher, token: str, msgpack: bool = True) -> None:
        self._session = session
        self.__token = token
        self._msgpack = msgpack and HAS_MSGPACK
        self._dispatch = dispatch
        self.ws: ClientWebSocketResponse
    
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
    
    async def poll(self) -> None:
        msg = await self.ws.receive()

        if msg.type is WSMsgType.BINARY or msg.type is WSMsgType.TEXT:
            ...
        elif msg.type is WSMsgType.ERROR:
            raise msg.data
        else:
            raise AttemptReconnect
    
    async def connect(self) -> None:
        self.ws = await self._session.ws_connect(DEFAULT_WS_URL)

        await self.poll()

        await self.send({
            "op": "identify",
            "token": self.__token,
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
            except Exception as e:
                if not self.ws.closed:
                    await self.ws.close()
                
                raise e
