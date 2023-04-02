from __future__ import annotations

import aiohttp
import asyncio

from typing import Literal, TYPE_CHECKING

from .server import AdaptServer
from .util import extract_user_id_from_token, _bytes_to_image_data, MISSING

if TYPE_CHECKING:
    from typing import Any, Final, TypeAlias, Self

    from .types.channel import (
        Channel,
        DMChannel,
        GuildChannel,
        GuildChannelType,
        CreateGuildChannelPayload,
        CreateDMChannelPayload,
    )
    from .types.user import (
        CreateUserPayload,
        CreateUserResponse,
        EditUserPayload,
        SendFriendRequestPayload,
        LoginRequest,
        LoginResponse,
        TokenRetrievalMethod,
        ClientUser,
        User,
        Relationship,
    )

DEFAULT_API_URL: Final[str] = AdaptServer.production().api

RequestMethod: TypeAlias = Literal['GET', 'POST', 'PATCH', 'PUT', 'DELETE']


class HTTPClient:
    """Represents an HTTP client that makes requests to Adapt over HTTP."""

    __slots__ = ('loop', 'session', 'client_id', 'server_url', '_token')

    def __init__(
        self,
        *,
        loop: asyncio.AbstractEventLoop | None = None,
        session: aiohttp.ClientSession | None = None,
        server_url: str = DEFAULT_API_URL,
        token: str | None = None,
        **kwargs,
    ) -> None:
        self.loop = loop or asyncio.get_event_loop()
        self.session = session or aiohttp.ClientSession(**kwargs, loop=self.loop)

        self.client_id: int | None = extract_user_id_from_token(token) if token is not None else None
        self.server_url: str = server_url.removesuffix('/')
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
        json: Any = None,
    ) -> Any:
        headers = headers or {}
        if self.token is not None:
            headers['Authorization'] = self.token

        if json is not None:
            headers['Content-Type'] = 'application/json'

        endpoint = '/' + endpoint.removeprefix('/')
        async with self.session.request(
            method,
            self.server_url + endpoint,
            headers=headers,
            params=params,
            json=json,
        ) as response:
            # TODO: Proper ratelimit handling and error handling
            response.raise_for_status()
            return await response.json()

    # Auth

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

    # Users

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

    async def get_user(self, user_id: int) -> User:
        return await self.request('GET', f'/users/{user_id}')

    async def get_authenticated_user(self) -> ClientUser:
        return await self.request('GET', '/users/me')

    async def edit_authenticated_user(
        self,
        *,
        username: str = MISSING,
        avatar: bytes | None = MISSING,
        banner: bytes | None = MISSING,
        bio: str | None = MISSING,
    ) -> ClientUser:
        payload: EditUserPayload = {'username': username}
        if avatar is not MISSING:
            payload['avatar'] = _bytes_to_image_data(avatar)
        if banner is not MISSING:
            payload['banner'] = _bytes_to_image_data(banner)
        if bio is not MISSING:
            payload['bio'] = bio

        return await self.request('PATCH', '/users/me', json=payload)

    async def delete_authenticated_user(self) -> None:
        await self.request('DELETE', '/users/me')

    async def get_relationships(self) -> list[Relationship]:
        return await self.request('GET', '/relationships')

    async def send_friend_request(self, *, username: str, discriminator: int) -> Relationship:
        payload: SendFriendRequestPayload = {
            'username': username,
            'discriminator': discriminator,
        }
        return await self.request('POST', '/relationships/friends', json=payload)

    async def accept_friend_request(self, user_id: int) -> Relationship:
        return await self.request('PUT', f'/relationships/friends/{user_id}')

    async def block_user(self, user_id: int) -> Relationship:
        return await self.request('PUT', f'/relationships/blocks/{user_id}')

    async def delete_relationship(self, user_id: int) -> None:
        await self.request('DELETE', f'/relationships/{user_id}')

    # Channels

    async def get_channel(self, channel_id: int) -> Channel:
        return await self.request('GET', f'/channels/{channel_id}')

    # TODO async def edit_channel

    async def delete_channel(self, channel_id: int) -> None:
        await self.request('DELETE', f'/channels/{channel_id}')

    async def get_guild_channels(self, guild_id: int) -> list[GuildChannel]:
        return await self.request('GET', f'/guilds/{guild_id}/channels')

    # TODO async def create_guild_channel

    async def get_dm_channels(self) -> list[DMChannel]:
        return await self.request('GET', '/users/me/channels')

    async def create_user_dm_channel(self, recipient_id: int) -> DMChannel:
        payload: CreateDMChannelPayload = {
            'type': 'dm',
            'recipient_id': recipient_id,
        }
        return await self.request('POST', '/users/me/channels', json=payload)

    async def create_group_dm_channel(self, *, name: str, recipient_ids: list[int]) -> DMChannel:
        payload: CreateDMChannelPayload = {
            'type': 'group',
            'name': name,
            'recipient_ids': recipient_ids,
        }
        return await self.request('POST', '/users/me/channels', json=payload)

    async def close(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()
