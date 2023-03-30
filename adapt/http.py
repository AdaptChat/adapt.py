from __future__ import annotations

import aiohttp
import asyncio

from typing import Literal, TYPE_CHECKING

from .util import extract_user_id_from_token

if TYPE_CHECKING:
    from typing import Any, Final, TypeAlias, Self, TypedDict

    from .types.user import TokenRetrievalMethod, LoginRequest, LoginResponse, CreateUserPayload, CreateUserResponse

DEFAULT_API_URL: Final[str] = 'https://api.adapt.chat'

RequestMethod: TypeAlias = Literal['GET', 'POST', 'PATCH', 'PUT', 'DELETE']


class HTTPClient:
    """Represents an HTTP client that makes requests to Adapt over HTTP."""

    __slots__ = ('loop', 'session', 'client_id', 'server_uri', '_token')

    def __init__(
        self,
        *,
        loop: asyncio.AbstractEventLoop | None = None,
        session: aiohttp.ClientSession | None = None,
        server_uri: str = DEFAULT_API_URL,
        token: str | None = None,
        **kwargs,
    ) -> None:
        self.loop = loop or asyncio.get_event_loop()
        self.session = session or aiohttp.ClientSession(**kwargs, loop=self.loop)

        self.client_id: int | None = extract_user_id_from_token(token) if token is not None else None
        self.server_uri: str = server_uri.removesuffix('/')
        self._token: str | None = token

    @property
    def token(self) -> str | None:
        """The token used to authenticate requests."""
        return self._token

    @token.setter
    def token(self, value: str | None) -> None:
        self._token = value
        self.client_id = extract_user_id_from_token(value) if value is not None else None

    @token.deleter
    def token(self) -> None:
        self._token = None
        self.client_id = None

    async def request(
        self,
        method: RequestMethod,
        endpoint: str,
        *,
        headers: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        json: TypedDict | None = None,
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

    async def login(self, *, email: str, password: str, method: TokenRetrievalMethod = 'reuse') -> LoginResponse:
        payload: LoginRequest = {
            'email': email,
            'password': password,
            'method': method,
        }
        response: LoginResponse = await self.request('POST', '/login', json=payload)
        self.client_id = response['user_id']
        self.token = response['token']
        return response

    async def create_user(self, *, username: str, email: str, password: str) -> CreateUserResponse:
        payload: CreateUserPayload = {
            'username': username,
            'email': email,
            'password': password,
        }
        response: CreateUserResponse = await self.request('POST', '/users', json=payload)
        self.client_id = response['id']
        self.token = response['token']
        return response

    async def close(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()
