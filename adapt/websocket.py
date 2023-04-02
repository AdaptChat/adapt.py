from __future__ import annotations

import asyncio
import json
import time
from typing import TYPE_CHECKING

from aiohttp import WSMsgType

from .server import AdaptServer
from .util import MISSING

if TYPE_CHECKING:
    from asyncio import Task
    from typing import Any, Callable, TypedDict, TypeAlias, Final

    from aiohttp import ClientWebSocketResponse

    from .connection import Connection
    from .models.enums import Status
    from .types.ws import InboundMessage

    Dispatcher: TypeAlias = Callable[..., Task[list[Any]]]

try:
    import msgpack
except ModuleNotFoundError:
    HAS_MSGPACK = False
else:
    HAS_MSGPACK = True

DEFAULT_WS_URL: Final[str] = AdaptServer.production().harmony


class HeartbeatManager:
    """Manages and acks heartbeats from and to harmony."""

    __slots__ = (
        '_ws',
        '_connection',
        'acked',
        '_is_active',
        '_task',
        '_last_heartbeat',
        '_last_heartbeat_ack',
        '_heartbeat_interval',
        '_heartbeat_timeout',
    )

    def __init__(
        self,
        ws: WebSocket,
        /,
        *,
        heartbeat_interval: float = 15.0,
        heartbeat_timeout: float = 3.0,
    ) -> None:
        self._ws = ws
        self._connection = ws._connection
        self.acked = self._connection.loop.create_future()
        self._is_active = False

        self._heartbeat_interval = heartbeat_interval
        self._heartbeat_timeout = heartbeat_timeout
        self._last_heartbeat: int | None = None
        self._last_heartbeat_ack: int | None = None

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self._connection.loop

    @property
    def latency_ns(self) -> int | None:
        if self._last_heartbeat is None or self._last_heartbeat_ack is None:
            return None

        return self._last_heartbeat_ack - self._last_heartbeat

    def start(self) -> None:
        if self.is_active:
            return
        self.acked = self.loop.create_future()
        self._task = self.loop.create_task(self.heartbeat_task())
        self._is_active = True

    def ack(self) -> None:
        self._last_heartbeat_ack = time.perf_counter_ns()
        self.acked.set_result(True)
        self.acked = self.loop.create_future()

    async def stop(self) -> None:
        if not self.is_active:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._is_active = False

    async def heartbeat(self) -> None:
        await self._ws.send({"op": "ping"})
        self._last_heartbeat = time.perf_counter_ns()

    async def heartbeat_task(self) -> None:
        while not self._ws.closed:
            await self.heartbeat()
            try:
                await asyncio.wait_for(self.acked, timeout=self._heartbeat_timeout)
            except asyncio.TimeoutError:
                await self.stop()
                raise AttemptReconnect

            await asyncio.sleep(self._heartbeat_interval)


class AttemptReconnect(Exception):
    pass


class WebSocket:
    """The WebSocket client used to interact with Adapt's websocket, harmony."""

    __slots__ = (
        '_connection',
        '_loop',
        '_session',
        '_dispatch',
        '_token',
        '_msgpack',
        '_heartbeat_manager',
        'ws_url',
        'ws',
    )

    ws: ClientWebSocketResponse | None

    def __init__(
        self,
        connection: Connection,
        *,
        prefer_msgpack: bool = True,
        ws_url: str = DEFAULT_WS_URL,
        heartbeat_interval: float = 15.0,
        heartbeat_timeout: float = 3.0,
    ) -> None:
        self._connection = connection
        self._loop = connection.loop

        http = connection.http
        self._session = http.session
        self._dispatch = connection.dispatch
        self._token = http.token
        self._msgpack = prefer_msgpack and HAS_MSGPACK
        self._heartbeat_manager = HeartbeatManager(
            self,
            heartbeat_interval=heartbeat_interval,
            heartbeat_timeout=heartbeat_timeout,
        )

        self.ws_url = ws_url
        self.ws = None
        if prefer_msgpack:
            self.ws_url += '?format=msgpack'

    @property
    def closed(self) -> bool:
        return self.ws is None or self.ws.closed

    @property
    def latency(self) -> float | None:
        return self.latency_ns and self.latency_ns / 1_000_000_000

    @property
    def latency_ns(self) -> int | None:
        return self._heartbeat_manager.latency_ns

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

        if event == 'hello':
            self._heartbeat_manager.start()
        elif event == 'pong':
            self._heartbeat_manager.ack()

        self._connection.process_event(msg)

    async def poll(self) -> None:
        msg = await self.ws.receive()

        if msg.type is WSMsgType.BINARY or msg.type is WSMsgType.TEXT:
            await self.process_message(msg.data)
        elif msg.type is WSMsgType.ERROR:
            raise msg.data
        else:
            raise AttemptReconnect
    
    async def connect(self, *, reconnect: bool = False) -> None:
        self.ws = await self._session.ws_connect(self.ws_url)

        await self.poll()
        await self.send({
            "op": "identify",
            "token": self._token,
            "status": self._connection._connect_status.value,
            "device": "desktop",
        })
        self._dispatch("reconnect" if reconnect else "connect")

    async def update_presence(self, *, status: Status = MISSING) -> None:
        payload = {"op": "update_presence"}
        if status is not MISSING:
            payload["status"] = status.value

        await self.send(payload)
    
    async def start(self) -> None:
        await self.connect()

        while True:
            try:
                await self.poll()
            except AttemptReconnect:
                await self.connect(reconnect=True)
                continue
            except Exception:
                if not self.ws.closed:
                    await self.ws.close()
                    self._dispatch("disconnect")
                    await self._heartbeat_manager.stop()
                raise

    async def close(self) -> bool:
        await self._heartbeat_manager.stop()
        if self.ws is not None:
            return await self.ws.close(code=1000)
        return False
