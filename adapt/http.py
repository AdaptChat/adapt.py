from __future__ import annotations

import aiohttp
import asyncio

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Final, Literal, TypeAlias, Self

    from .types.user import TokenRetrievalMethod, LoginRequest, LoginResponse

DEFAULT_API_URL: Final[str] = 'https://api.adapt.chat'

RequestMethod: TypeAlias = Literal['GET', 'POST', 'PATCH', 'PUT', 'DELETE']


class HTTPClient:
    """Represents an HTTP client that makes requests to Adapt over HTTP."""

    __slots__ = ('loop', 'session', 'client_id', 'token', 'server_uri')

    def __init__(
        self,
        *,
        loop: asyncio.AbstractEventLoop | None = None,
        session: aiohttp.ClientSession | None = None,
        server_uri: str = DEFAULT_API_URL,
        **kwargs,
    ) -> None:
        self.loop = loop or asyncio.get_event_loop()
        self.session = session or aiohttp.ClientSession(**kwargs, loop=self.loop)

        self.client_id: int | None = None
        self.token: str | None = None
        self.server_uri: str = server_uri.removesuffix('/')

    async def request(
        self,
        method: RequestMethod,
        endpoint: str,
        *,
        headers: dict[str, Any] = None,
        params: dict[str, Any] = None,
        json: dict[str, Any] = None,
    ) -> Any:
        headers = headers or {}
        if self.token is not None:
            headers['Authorization'] = self.token

        if json is not None:
            headers['Content-Type'] = 'application/json'

        endpoint = '/' + endpoint.removeprefix('/')
        async with self.session.request(
            method,
            self.server_uri + endpoint,
            headers=headers,
            params=params,
            json=json,
        ) as response:
            # TODO: Proper ratelimit handling and error handling
            response.raise_for_status()
            return await response.json()

    async def login(
        self,
        *,
        email: str,
        password: str,
        method: TokenRetrievalMethod = 'reuse',
    ) -> LoginResponse:
        payload: LoginRequest = {
            'email': email,
            'password': password,
            'method': method,
        }
        response: LoginResponse = await self.request('POST', '/login', json=payload)
        self.client_id = response['id']
        self.token = response['token']

        return response

    async def close(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()
