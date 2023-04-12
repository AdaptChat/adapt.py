from __future__ import annotations

import asyncio
import time
from typing import Awaitable, Callable, Generic, ParamSpec, TypeVar, TYPE_CHECKING

import aiohttp

from .connection import Connection
from .http import HTTPClient
from .models.enums import Status
from .models.guild import PartialGuild
from .models.user import PartialUser
from .polyfill import removeprefix
from .server import AdaptServer
from .util import maybe_coro, IS_DOCUMENTING, MISSING
from .websocket import WebSocket

if TYPE_CHECKING:
    from typing import Any, Generator, Iterable, Self, ValuesView, TypeAlias

    from .models.message import Message
    from .models.ready import ReadyEvent
    from .models.guild import Guild
    from .models.user import ClientUser, Relationship, User
    from .types.user import TokenRetrievalMethod
    from .util import IOSource

P = ParamSpec('P')
R = TypeVar('R')
ClientT = TypeVar('ClientT', bound='Client')
EventListener: TypeAlias = Callable[P, Awaitable[R] | R]


class _CoroutineWrapper(Generic[ClientT]):
    __slots__ = ('coro', '_client')

    def __init__(self, coro: Awaitable[ClientT]) -> None:
        self.coro = coro
        self._client: ClientT | None = None

    def __await__(self) -> Generator[Any, None, ClientT]:
        return self.coro.__await__()

    async def __aenter__(self) -> ClientT:
        client = self._client = await self.coro
        return await client.__aenter__()

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._client is not None:
            return await self._client.__aexit__(exc_type, exc, tb)


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

        if getattr(self.callback, '__adapt_call_once__', False):
            self.destroy()

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

    if TYPE_CHECKING or IS_DOCUMENTING:
        async def on_event(self, event: str, *args: Any, **kwargs: Any) -> None:
            """|coro|

            A "catch all" event handler for all events.

            Parameters
            ----------
            event: :class:`str`
                The name of the event.
            *args: Any
                The positional arguments for the event.
            **kwargs: Any
                The keyword arguments for the event.
            """

        async def on_start(self) -> None:
            """|coro|

            Called when the client starts to connect. This can be used to perform any necessary setup.
            """

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

        async def on_guild_create(self, guild: Guild) -> None:
            """|coro|

            Called when a guild is created.

            Parameters
            ----------
            guild: :class:`.Guild`
                The guild that was created.
            """

        async def on_message(self, message: Message) -> None:
            """|coro|

            Called when a message is created.

            Parameters
            ----------
            message: :class:`.Message`
                The message that was created.
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

            events = events or (callback.__name__,)
            events = tuple(removeprefix(event.lower(), 'on_') for event in events)

            def event_check(event: str) -> bool:
                return removeprefix(event, 'on_') in events

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

    def _dispatch_event(self, event: str, *args, **kwargs) -> asyncio.Task[list[Any]]:
        coros = []
        if callback := getattr(self, 'on_' + event, None):
            assert callable(callback), f'Event listener for {event} is not callable'

            if getattr(callback, '__adapt_call_once__', False):
                setattr(self, 'on_' + event, None)

            coros.append(maybe_coro(callback, *args, **kwargs))

        coros.extend(listener.dispatch(event, *args, **kwargs) for listener in self._weak_listeners)
        return asyncio.ensure_future(asyncio.gather(*coros))

    def dispatch(self, event: str, *args, **kwargs) -> asyncio.Task[list[Any]]:
        """Dispatches an event to its registered listeners.

        Parameters
        ----------
        event: :class:`str`
            The event to dispatch to.
        *args
            Positional arguments to pass into event handlers.
        **kwargs
            Keyword arguments to pass into event handlers.
        """
        self._dispatch_event('event', event, *args, **kwargs)
        return self._dispatch_event(event, *args, **kwargs)

    async def wait_for(
        self,
        *events: str,
        check: Callable[P, bool | Awaitable[bool]] | None = None,
        timeout: float | None = None,
    ) -> P.args:
        """|coro|

        Waits for an event to be dispatched.

        Parameters
        ----------
        *events: :class:`str`
            The events to listen for.
        check: ((*P.args, **P.kwargs) -> :class:`bool`) | None
            An event check for when to call the callback. Leave empty to not have a check.
        timeout: :class:`float` | None
            The amount of seconds before this listener should expire. Leave empty to not have a timeout.

        Raises
        ------
        :exc:`asyncio.TimeoutError`
            The event was not dispatched within the given timeout.

        Returns
        -------
        *P.args
            The positional arguments of the dispatched event.
        """
        params = asyncio.Future()

        @self.listen(*events, check=check, timeout=timeout)
        @once
        def callback(*c_args, **c_kwargs):
            params.set_result((c_args, c_kwargs))

        try:
            result = await asyncio.wait_for(params, timeout=timeout)
        except asyncio.TimeoutError:
            raise
        else:
            args, kwargs = result
            if args and kwargs:
                return result
            elif args:
                return args[0] if len(args) == 1 else args
            elif kwargs:
                return kwargs


class Client(EventDispatcher):
    """Represents a client that interacts with Adapt.

    This class inherits from :class:`~.client.EventDispatcher`. See the documentation for that class for documentation
    on event listeners.

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
    status: :class:`.Status`
        The status to set the client to when it connects to harmony. Defaults to :attr:`.Status.online`.
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
        status: Status = Status.online,
    ) -> None:
        self._server = server
        self.loop = loop or asyncio.get_event_loop()
        self.http = HTTPClient(loop=self.loop, session=session, server_url=server.api, token=token)

        self._prepare_client(status=status)
        super().__init__()

    def _prepare_client(self, **options: Any) -> None:
        self.ws = None
        self._connection = Connection(
            http=self.http,
            server=self._server,
            loop=self.loop,
            dispatch=self.dispatch,
            **options,
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
        """:class:`~.connection.Connection`: The connection object that manages the connection to Adapt and cached models."""
        return self._connection

    @property
    def latency(self) -> float | None:
        """:class:`float`: The amount of time in seconds it took for the previous heartbeat to harmony (the websocket)
        to be acknowledged.

        This is ``None`` if:
        - The client is not logged in.
        - The client has not yet sent a heartbeat to harmony.
        - The client has not yet received a heartbeat acknowledgement from harmony.
        """
        return self.ws and self.ws.latency

    @property
    def latency_ns(self) -> int | None:
        """:class:`int`: The equivalent of :attr:`.latency` but in nanoseconds. This could yield more accurate
        measurements due to floating point precision errors in :attr:`.latency`.

        See Also
        --------
        :attr:`.latency`
            The equivalent of this property in seconds. See this for more information.
        """
        return self.ws and self.ws.latency_ns

    @property
    def user(self) -> ClientUser | None:
        """:class:`.ClientUser` | None: The user object that represents the user account the client is logged into.

        This is ``None`` if the client is not logged in.
        """
        return self._connection.user

    @property
    def users(self) -> ValuesView[User]:
        """Iterable[:class:`.User`]: An iterable of users that the client has cached."""
        return self._connection._users.values()

    @property
    def guilds(self) -> ValuesView[Guild]:
        """Iterable[:class:`.Guild`]: An iterable of guilds that the client has cached."""
        return self._connection._guilds.values()

    @property
    def relationships(self) -> ValuesView[Relationship]:
        """Iterable[:class:`.Relationship`]: An iterable of relationships that the client has cached."""
        return self._connection._relationships.values()

    @property
    def is_ready(self) -> bool:
        """:class:`bool`: Whether the client has received the ready event from harmony yet."""
        return self._connection._is_ready.done()

    async def wait_until_ready(self) -> ReadyEvent:
        """|coro|

        Blocks the event loop until the client receives the ready event from harmony.

        Returns
        -------
        :class:`.ReadyEvent`
            The ready event that was dispatched.
        """
        return await self._connection._is_ready

    def get_user(self, user_id: int) -> User | None:
        """Retrieves a user from the cache.

        Parameters
        ----------
        user_id: :class:`int`
            The user ID to retrieve.

        Returns
        -------
        :class:`.User` | None
            The user object that was retrieved, or ``None`` if no user was found.
        """
        return self._connection.get_user(user_id)

    def get_partial_user(self, user_id: int) -> PartialUser:
        """Creates a usable partial user object that operates with only its ID.

        This is useful for when you want to perform actions on a user without having to ensure they are cached
        or fetch unnecessary user data.

        Parameters
        ----------
        user_id: :class:`int`
            The user ID to create the partial user with.

        Returns
        -------
        :class:`.PartialUser`
            The partial user object that was created.
        """
        return PartialUser(connection=self._connection, id=user_id)

    async def fetch_user(self, user_id: int, *, respect_cache: bool = False) -> User:
        """|coro|

        Fetches a user directly from the API.

        Parameters
        ----------
        user_id: :class:`int`
            The user ID to fetch.
        respect_cache: :class:`bool`
            If ``True``, if the user is found in the cache, it will be returned instead of fetching from the API.

        Returns
        -------
        :class:`.User` | None
            The user object that was fetched, or ``None`` if no user was found.
        """
        if cached := respect_cache and self.get_user(user_id):
            return cached

        return self._connection.add_raw_user(await self.http.get_user(user_id))

    def get_relationship(self, user_id: int) -> Relationship | None:
        """Retrieves the relationship between the client and the user with the given ID from the cache.

        Parameters
        ----------
        user_id: :class:`int`
            The user ID to retrieve.

        Returns
        -------
        :class:`.Relationship`
            The relationship object that was retrieved, or ``None`` if no relationship was found.
        """
        return self._connection.get_relationship(user_id)

    async def fetch_relationships(self) -> Iterable[Relationship]:
        """|coro|

        Fetches all relationships between the client and other users directly from the API.

        Returns
        -------
        Iterable[:class:`.Relationship`]
            An iterable of relationship objects that were fetched. This is a generator that lazily resolves the
            relationships into :class:`.Relationship` objects.
        """
        relationships = await self.http.get_relationships()
        return map(self._connection.update_raw_relationship, relationships)

    def get_guild(self, guild_id: int) -> Guild | None:
        """Retrieves a guild from the cache.

        Parameters
        ----------
        guild_id: :class:`int`
            The guild ID to retrieve.

        Returns
        -------
        :class:`.Guild` | None
            The guild object that was retrieved, or ``None`` if no guild was found.
        """
        return self._connection.get_guild(guild_id)

    def get_partial_guild(self, guild_id: int) -> PartialGuild:
        """Creates a usable partial guild object that operates with only its ID.

        This is useful for when you want to perform actions on a guild without having to ensure it is cached
        or fetch unnecessary guild data.

        Parameters
        ----------
        guild_id: :class:`int`
            The guild ID to create the partial guild with.

        Returns
        -------
        :class:`.PartialGuild`
            The partial guild object that was created.
        """
        return PartialGuild(connection=self._connection, id=guild_id)

    async def fetch_guild(
        self,
        guild_id: int,
        *,
        respect_cache: bool = False,
        channels: bool = False,
        members: bool = False,
        roles: bool = False,
    ) -> Guild:
        """|coro|

        Fetches a guild directly from the API.

        Parameters
        ----------
        guild_id: :class:`int`
            The guild ID to fetch.
        respect_cache: :class:`bool`
            If ``True``, if the guild is found in the cache, it will be returned instead of fetching from the API.
            This will also mean the ``members``, ``roles``, and ``channels`` parameters will be ignored.
        channels: :class:`bool`
            If ``True``, the guild's channels will be fetched.
        members: :class:`bool`
            If ``True``, the guild's members will be fetched.
        roles: :class:`bool`
            If ``True``, the guild's roles will be fetched.

        Returns
        -------
        :class:`.Guild`
            The guild object that was fetched.
        """
        if cached := respect_cache and self.get_guild(guild_id):
            return cached

        return self._connection.add_raw_guild(
            await self.http.get_guild(guild_id, channels=channels, members=members, roles=roles),
        )

    async def fetch_guilds(
        self, *, channels: bool = False, members: bool = False, roles: bool = False,
    ) -> Iterable[Guild]:
        """|coro|

        Fetches all guilds that the client is a member of.

        .. warning::
            This is an expensive process and has high ratelimits, so it should be used sparingly.
            Guild data is returned by the ready event, so it is usually unnecessary to call this method.

        Parameters
        ----------
        channels: :class:`bool`
            If ``True``, channel data will be fetched for each guild.
        members: :class:`bool`
            If ``True``, member data will be fetched for each guild.
        roles: :class:`bool`
            If ``True``, role data will be fetched for each guild.

        Returns
        -------
        Iterable[:class:`.Guild`]
            An iterable of guild objects that were fetched. This is a generator that lazily resolves the
            guilds into :class:`.Guild` objects.
        """
        guilds = await self.http.get_guilds(channels=channels, members=members, roles=roles)
        return map(self._connection.add_raw_guild, guilds)

    async def create_guild(
        self,
        *,
        name: str,
        description: str | None = None,
        icon: IOSource | None = None,
        banner: IOSource | None = None,
        public: bool = False,
        nonce: str | None = None,
    ) -> Guild:
        """|coro|

        Creates a new guild.

        Parameters
        ----------
        name: :class:`str`
            The name of the guild.
        description: :class:`str`
            The description of the guild. This is optional.
        icon: :class:`bytes`, path-like object, file-like object, or ``None``
            The icon of the guild. This is optional.
        banner: :class:`bytes`, path-like object, file-like object, or ``None``
            The banner of the guild. This is optional.
        public: :class:`bool`
            Whether the guild should be public. Defaults to ``False``.
        nonce: :class:`str`
            An optional nonce for integrity. When the guild creation event is received through the websocket, the nonce
            will be included in the payload. This can be used to verify that the guild was created successfully.

        Returns
        -------
        :class:`.Guild`
            The guild that was created.
        """
        data = await self.http.create_guild(
            name=name,
            description=description,
            icon=icon,
            banner=banner,
            public=public,
            nonce=nonce,
        )
        return self._connection.add_raw_guild(data)

    async def update_presence(self, *, status: Status = MISSING) -> None:
        """|coro|

        Updates the client's presence.

        Parameters
        ----------
        status: :class:`.Status`
            The new status to update the client's presence with. Leave blank to keep the current status.
        """
        await self.ws.update_presence(status=status)

    @classmethod
    def from_http(cls, http: HTTPClient, *, server: AdaptServer | None = None, **kwargs: Any) -> Self:
        """Creates a client from an HTTP client. This is used internally.

        Parameters
        ----------
        http: :class:`~.http.HTTPClient`
            The HTTP client to create the client object with.
        server: :class:`.AdaptServer`
            The urls of the backend server. Defaults to the production server found at `adapt.chat`.
        **kwargs
            Additional keyword arguments to pass into the client constructor.

        Returns
        -------
        :class:`~.Client`
            The created client object.
        """

        self = cls.__new__(cls)
        self.loop = http.loop
        self.http = http
        self._server = server or AdaptServer.production().copy_with(api=http.server_url)

        self._prepare_client(**kwargs)
        super(Client, self).__init__()
        return self

    @classmethod
    def from_login(
        cls,
        *,
        email: str,
        password: str,
        method: TokenRetrievalMethod = 'reuse',
        server: AdaptServer = AdaptServer.production(),
        **options: Any,
    ) -> _CoroutineWrapper[Self]:
        """|coro|

        Logs in with the specified credentials, then returns a client to interact with that account.

        When using this in a context manager, ``async with await`` is unnecessary ::

            # Recommended:
            async with Client.from_login(...) as client:
                await client.start(TOKEN)

            # Unnecessary:
            async with await Client.from_login(...) as client:
                await client.start(TOKEN)

        Otherwise, this should be treated as a coroutine: ::

            client = await Client.from_login(...)
            client.run(TOKEN)

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
        async def coro() -> Self:
            http = HTTPClient(**options, server_url=server.api)
            await http.login(email=email, password=password, method=method)
            return cls.from_http(http, server=server)

        return _CoroutineWrapper(coro())

    @classmethod
    def create_user(
        cls,
        *,
        username: str,
        email: str,
        password: str,
        server: AdaptServer = AdaptServer.production(),
        **options: Any,
    ) -> _CoroutineWrapper[Self]:
        """|coro|

        Registers a new user account, and returns a new client created to interact with that account.

        When using this in a context manager, ``async with await`` is unnecessary ::

            # Recommended:
            async with Client.create_user(...) as client:
                await client.start(TOKEN)

            # Unnecessary:
            async with await Client.create_user(...) as client:
                await client.start(TOKEN)

        Otherwise, this should be treated as a coroutine: ::

            client = await Client.create_user(...)
            client.run(TOKEN)

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
        async def coro() -> Self:
            http = HTTPClient(**options, server_url=server.api)
            await http.create_user(username=username, email=email, password=password)
            return cls.from_http(http, server=server)

        return _CoroutineWrapper(coro())

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
        self.ws = WebSocket(self.connection, ws_url=self.server.harmony)
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

    Usage: ::

        from adapt import Client, ReadyEvent, once

        class MyClient(Client):
            @once
            async def on_ready(self, _event: ReadyEvent):
                print('Ready!')

    Parameters
    ----------
    func: (*P.args, **P.kwargs) -> Any
        The event listener.

    Returns
    -------
    (*P.args, **P.kwargs) -> Any
        The event listener that will be called only once.
    """
    func.__adapt_call_once__ = True
    return func
