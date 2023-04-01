from __future__ import annotations

import asyncio
import time
from typing import Awaitable, Callable, Generic, ParamSpec, TypeVar, TYPE_CHECKING

import aiohttp

from .connection import Connection
from .http import HTTPClient
from .server import AdaptServer
from .util import maybe_coro
from .websocket import WebSocket

if TYPE_CHECKING:
    from typing import Any, Self, TypeAlias

    from .models.ready import ReadyEvent
    from .types.user import TokenRetrievalMethod

P = ParamSpec('P')
R = TypeVar('R')
EventListener: TypeAlias = Callable[P, Awaitable[R] | R]


class WeakEventRegistry(Generic[P, R]):
    """Receives events until the specified limit or timeout.

    Parameters
    ----------
    event_check: (str) -> bool
        The predicate performed on event names.
    check: (*P.args, **P.kwargs) -> bool
        The predicate performed on the event.
    """

    def __init__(
        self,
        registry: list[Self],
        callback: EventListener[P, R],
        *,
        event_check: Callable[[str], bool | Awaitable[bool]] | None = None,
        check: Callable[P, bool | Awaitable[bool]] | None = None,
        timeout: float | None = None,
        limit: int | None = None,
    ) -> None:
        self._registry = registry
        self._event_check = event_check
        self._destroy = timeout and time.perf_counter() + timeout

        self.check = check
        self.callback = callback
        self.remaining = limit

    def destroy(self) -> None:
        """Destroys this listener."""
        try:
            self._registry.remove(self)
        except ValueError:
            pass

    async def dispatch(self, event: str, *args: P.args, **kwargs: P.kwargs) -> None:
        """|coro|

        Dispatches an event with the given arguments.
        """

        if self._destroy and time.perf_counter() >= self._destroy:
            return self.destroy()

        if self._event_check and not self._event_check(event):
            return

        if self.check and not await maybe_coro(self.check, *args, **kwargs):
            return

        if self.remaining is not None:
            self.remaining -= 1
            if self.remaining < 0:
                return self.destroy()

        await maybe_coro(self.callback, *args, **kwargs)


class EventDispatcher:
    """Base class for receiving events and then dispatching them to event handlers registered on the client."""

    if TYPE_CHECKING:
        async def on_connect(self) -> None:
            """|coro|

            Called when the client establishes a connection with the websocket.
            """

        async def on_ready(self, ready: ReadyEvent) -> None:
            """|coro|

            Called when the client is connected and ready to receive events from the websocket.

            Parameters
            ----------
            ready: :class:`.ReadyEvent`
                Data received with the ready event.
            """

    def __init__(self) -> None:
        self._weak_listeners: list[WeakEventRegistry] = []

    def event(self, callback: EventListener[P, R]) -> EventListener[P, R]:
        """Registers an event listener on the client. This overrides any previous listeners for that event."""

        event = callback.__name__
        if not event.startswith('on_'):
            event = 'on_' + event

        setattr(self, event, callback)
        return callback

    def listen(
        self,
        *events: str,
        check: Callable[P, bool | Awaitable[bool]] | None = None,
        timeout: float | None = None,
        limit: int | None = None,
    ) -> Callable[[EventListener[P, R]], EventListener[P, R]]:
        """Registers a weak listener for the given events. You may register as many of these as you want.

        Parameters
        ----------
        *events: :class:`str`
            The events to listen for.
        check: ((*P.args, **P.kwargs) -> :class:`bool`) | None
            An event check for when to call the callback. Leave empty to not have a check.
        timeout: :class:`float` | None
            The amount of seconds before this listener should expire. Leave empty to not have a timeout.
        limit: :class:`int` | None
            The amount of times the callback should be called before this listener should expire.
            Leave empty to not have a limit.
        """
        def decorator(callback: EventListener[P, R]) -> EventListener[P, R]:
            nonlocal events
            nonlocal limit

            events = events or (callback.__name__,)
            events = tuple(event.lower().removeprefix('on_') for event in events)

            if getattr(callback, '__adapt_call_once__', False):
                if limit is not None:
                    raise ValueError('Cannot use limit kwarg and @once decorator at the same time.')
                limit = 1

            def event_check(event: str) -> bool:
                return event.removeprefix('on_') in events

            self._weak_listeners.append(WeakEventRegistry(
                self._weak_listeners,
                callback,  # type: ignore
                event_check=event_check,
                check=check,
                timeout=timeout,
                limit=limit,
            ))
            return callback

        return decorator
    
    def dispatch(self, event: str, *args, **kwargs) -> asyncio.Task[list[Any]]:
        """Dispatches an event to its registered listeners.

        Parameters
        ----------
        event: :class:`str:
            The event to dispatch to.
        *args
            Positional arguments to pass into event handlers.
        **kwargs
            Keyword arguments to pass into event handlers.
        """
        coros = []
        if callback := getattr(self, 'on_' + event, None):
            assert callable(callback), f'Event listener for {event} is not callable'

            if getattr(callback, '__adapt_call_once__', False):
                setattr(self, 'on_' + event, None)

            coros.append(maybe_coro(callback, *args, **kwargs))

        coros.extend(listener.dispatch(event, *args, **kwargs) for listener in self._weak_listeners)
        return asyncio.ensure_future(asyncio.gather(*coros))


class Client(EventDispatcher):
    """Represents a client that interacts with Adapt.

    Attributes
    ----------
    loop: :class:`asyncio.AbstractEventLoop`
        The asyncio event loop the client uses.
    http: :class:`~.http.HTTPClient`
        The HTTP client utilized by this client that interacts with Adapt HTTP requests.
    ws: :class:`~.ws.WebSocket`
        The websocket client utilized by this client that interacts with Adapt websocket events.

    Parameters
    ----------
    loop: :class:`asyncio.AbstractEventLoop`
        The event loop the client should use. Defaults to what is returned by calling :func:`asyncio.get_event_loop`.
    session: :class:`aiohttp.ClientSession`
        The aiohttp client session to use for the created HTTP client. If not provided, one is created for you.
    server: :class:`.AdaptServer`
        The urls of the backend server. Defaults to the production server found at `adapt.chat`.
    token: :class:`str`
        The token to run the client with. Leave blank to delay specification of the token.
    """

    if TYPE_CHECKING:
        ws: WebSocket | None
        _connection: Connection

    def __init__(
        self,
        *,
        loop: asyncio.AbstractEventLoop | None = None,
        session: aiohttp.ClientSession | None = None,
        server: AdaptServer = AdaptServer.production(),
        token: str | None = None,
    ) -> None:
        self._server = server
        self.loop = loop or asyncio.get_event_loop()
        self.http = HTTPClient(loop=self.loop, session=session, server_url=server.api, token=token)

        self._prepare_client()
        super().__init__()

    def _prepare_client(self, **connection_options: Any) -> None:
        self.ws = None
        self._connection = Connection(
            http=self.http,
            server=self._server,
            loop=self.loop,
            dispatch=self.dispatch,
            **connection_options,
        )

    @property
    def server(self) -> AdaptServer:
        """The server the client retrieves all Adapt URLs from."""
        return self._server

    @server.setter
    def server(self, value: AdaptServer) -> None:
        self._server = value
        self.http.server_url = value.api

        if self.ws is not None:
            self.ws.ws_url = value.harmony

    @property
    def connection(self) -> Connection:
        """The connection object that manages the connection to Adapt and cached models."""
        return self._connection

    @classmethod
    def from_http(cls, http: HTTPClient, *, server: AdaptServer | None = None) -> Self:
        """Creates a client from an HTTP client. This is used internally.

        Parameters
        ----------
        http: :class:`~.http.HTTPClient`
            The HTTP client to create the client object with.
        server: :class:`.AdaptServer`
            The urls of the backend server. Defaults to the production server found at `adapt.chat`.

        Returns
        -------
        :class:`~.Client`
            The created client object.
        """

        self = cls.__new__(cls)
        self.loop = http.loop
        self.http = http
        self._server = server or AdaptServer.production().copy_with(api=http.server_url)

        self._prepare_client()
        super(Client, self).__init__()
        return self

    @classmethod
    async def from_login(
        cls,
        *,
        email: str,
        password: str,
        method: TokenRetrievalMethod = 'reuse',
        server: AdaptServer = AdaptServer.production(),
        **options: Any,
    ) -> Self:
        """|coro|

        Logs in with the specified credentials, then returns a client to interact with that account.

        Parameters
        ----------
        email: :class:`str`
            The email of the account.
        password: :class:`str`
            The password of the account.
        method: Literal['new', 'revoke', 'reuse']
            The method to use to retrieve the token. Defaults to `'reuse'`.
        server: :class:`.AdaptServer`
            The urls of the backend server. Defaults to the production server found at `adapt.chat`.
        **options
            Additional keyword-arguments to pass in when constructing the HTTP client
            (i.e. `loop`, `session`)

        Returns
        -------
        :class:`~.Client`
            The created client object.
        """
        http = HTTPClient(**options, server_url=server.api)
        await http.login(email=email, password=password, method=method)
        return cls.from_http(http, server=server)

    @classmethod
    async def create_user(
        cls,
        *,
        username: str,
        email: str,
        password: str,
        server: AdaptServer = AdaptServer.production(),
        **options: Any,
    ) -> Self:
        """|coro|

        Registers a new user account, and returns a new client created to interact with that account.

        Parameters
        ----------
        username: :class:`str`
            The username of the new account.
        email: :class:`str`
            The email of the new account.
        password: :class:`str`
            The password of the new account.
        server: :class:`.AdaptServer`
            The urls of the backend server. Defaults to the production server found at `adapt.chat`.
        **options
            Additional keyword-arguments to pass in when constructing the HTTP client
            (i.e. `loop`, `session`)

        Returns
        -------
        :class:`~.Client`
            The created client object.
        """
        http = HTTPClient(**options, server_url=server.api)
        await http.create_user(username=username, email=email, password=password)
        return cls.from_http(http, server=server)

    async def start(self, token: str | None = None) -> None:
        """|coro|

        Starts the client, logging in with the provided token and connecting to harmony.

        Parameters
        ----------
        token: :class:`str`
            The token to log in with. If not provided, the token specified in the constructor is used.
        """
        self.http.token = token or self.http.token
        if not self.http.token:
            raise ValueError('No token provided to start the client with')

        self.dispatch('start')
        self.ws = WebSocket.from_connection(self.connection, dispatch=self.dispatch, ws_url=self.server.harmony)
        await self.ws.start()

    def run(self, token: str | None = None) -> None:
        """Runs the client, logging in with the provided token and connecting to harmony. This is a blocking call.

        Parameters
        ----------
        token: :class:`str`
            The token to log in with. If not provided, the token specified in the constructor is used.
        """
        async def runner() -> None:
            async with self:
                await self.start(token)

        try:
            self.loop.run_until_complete(runner())
        except KeyboardInterrupt:
            pass

    async def close(self) -> None:
        """|coro|

        Closes the client, freeing up resources the client might have used.
        This is automatically called if you use :meth:`~.Client.run`.
        """
        await self.http.close()

        if self.ws is not None:
            await self.ws.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()


def once(func: EventListener[P, R]) -> EventListener[P, R]:
    """A decorator that registers an event listener to be called only once before being destroyed.
    This can be used within the client class.

    Parameters
    ----------
    func: (*P.args, **P.kwargs) -> Any
        The event listener.

    Returns
    -------
    (*P.args, **P.kwargs) -> Any
        The event listener that will be called only once.

    Usage: ::

        from adapt import Client, ReadyEvent, once

        class MyClient(Client):
            @once
            async def on_ready(self, _event: ReadyEvent):
                print('Ready!')
    """
    func.__adapt_call_once__ = True
    return func
