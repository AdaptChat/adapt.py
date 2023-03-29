from __future__ import annotations

import asyncio
import time
from typing import Generic, ParamSpec, TypeVar, TYPE_CHECKING

import aiohttp

from .util import maybe_coro

if TYPE_CHECKING:
    from typing import Awaitable, Callable, Self, TypeAlias

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
        """Dispatches an event with the given arguments."""

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

        async def on_ready(self) -> None:
            """|coro|

            Called when the client is connected and ready to receive events from the websocket.
            """

    def __init__(self) -> None:
        self._weak_listeners: list[WeakEventRegistry] = []

    async def event(self, callback: EventListener[P, R]) -> EventListener[P, R]:
        """Registers an event listener on the client. This overrides any previous listeners for that event."""

        event = callback.__name__
        if not event.startswith('on_'):
            event = 'on_' + event

        setattr(self, event, callback)
        return callback

    async def listen(
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
            events = [event.lower().removeprefix('on_') for event in events]

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
    
    async def dispatch(self, event: str, *args, **kwargs) -> None:
        """Dispatches an event to its registered listeners."""
        coros = []
        if callback := getattr(self, 'on_' + event, None):
            assert callable(callback), f'Event listener for {event} is not callable'
            coros.append(maybe_coro(callback, *args, **kwargs))
            
        coros.extend(listener.dispatch(event, *args, **kwargs) for listener in self._weak_listeners)
        await asyncio.gather(*coros)


class Client(EventDispatcher):
    """Represents a client that interacts with Adapt."""
    
    def __init__(
        self,
        *,
        loop: asyncio.AbstractEventLoop | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self.loop = loop or asyncio.get_event_loop()

        super().__init__()
