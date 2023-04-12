from __future__ import annotations

import aiohttp
import asyncio

from typing import Literal, TYPE_CHECKING

from .polyfill import removeprefix, removesuffix
from .server import AdaptServer
from .util import extract_user_id_from_token, resolve_image, MISSING

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
    from .types.guild import (
        Guild,
        PartialGuild,
        CreateGuildPayload,
        EditGuildPayload,
        DeleteGuildPayload,
        Member,
        EditMemberPayload,
    )
    from .types.message import (
        Message,
        CreateMessagePayload,
        EditMessagePayload,
        MessageHistoryQuery,
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
    from .util import IOSource

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
        self.server_url: str = removesuffix(server_url, '/')
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

        endpoint = '/' + removeprefix(endpoint, '/')
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
        avatar: IOSource | None = MISSING,
        banner: IOSource | None = MISSING,
        bio: str | None = MISSING,
    ) -> ClientUser:
        payload: EditUserPayload = {'username': username}
        if avatar is not MISSING:
            payload['avatar'] = resolve_image(avatar)
        if banner is not MISSING:
            payload['banner'] = resolve_image(banner)
        if bio is not MISSING:
            payload['bio'] = bio

        return await self.request('PATCH', '/users/me', json=payload)

    async def delete_authenticated_user(self, *, password: str) -> None:
        await self.request('DELETE', '/users/me', json={'password': password})

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

    # Messages

    async def get_message_history(
        self,
        channel_id: int,
        *,
        before: int | None = None,
        after: int | None = None,
        limit: int = 100,
        user_id: int | None = None,
        oldest_first: bool = False,
    ) -> list[Message]:
        params: MessageHistoryQuery = {'oldest_first': oldest_first}
        if before is not None:
            params['before'] = before
        if after is not None:
            params['after'] = after
        if limit is not None:
            params['limit'] = limit
        if user_id is not None:
            params['user_id'] = user_id

        return await self.request('GET', f'/channels/{channel_id}/messages', params=params)

    async def get_message(self, channel_id: int, message_id: int) -> Message:
        return await self.request('GET', f'/channels/{channel_id}/messages/{message_id}')

    async def create_message(
        self,
        channel_id: int,
        *,
        content: str | None = None,
        nonce: str | None = None,
    ) -> Message:
        payload: CreateMessagePayload = {
            'content': content,
            'nonce': nonce,
        }
        return await self.request('POST', f'/channels/{channel_id}/messages', json=payload)

    async def edit_message(
        self,
        channel_id: int,
        message_id: int,
        *,
        content: str | None = MISSING,
    ) -> Message:
        payload: EditMessagePayload = {}
        if content is not MISSING:
            payload['content'] = content

        return await self.request('PATCH', f'/channels/{channel_id}/messages/{message_id}', json=payload)

    async def delete_message(self, channel_id: int, message_id: int) -> None:
        await self.request('DELETE', f'/channels/{channel_id}/messages/{message_id}')

    # Guilds

    async def get_guilds(self, *, channels: bool = False, members: bool = False, roles: bool = False) -> list[Guild]:
        return await self.request('GET', '/guilds', params={'channels': channels, 'members': members, 'roles': roles})

    async def get_guild(
        self,
        guild_id: int,
        *,
        channels: bool = False,
        members: bool = False,
        roles: bool = False,
    ) -> Guild:
        return await self.request(
            'GET',
            f'/guilds/{guild_id}',
            params={'channels': channels, 'members': members, 'roles': roles},
        )

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
        payload: CreateGuildPayload = {
            'name': name,
            'description': description,
            'public': public,
            'nonce': nonce,
        }
        if icon is not None:
            payload['icon'] = resolve_image(icon)
        if banner is not None:
            payload['banner'] = resolve_image(banner)

        return await self.request('POST', '/guilds', json=payload)

    async def edit_guild(
        self,
        guild_id: int,
        *,
        name: str = MISSING,
        description: str | None = MISSING,
        icon: IOSource | None = MISSING,
        banner: IOSource | None = MISSING,
        public: bool = MISSING,
    ) -> PartialGuild:
        payload: EditGuildPayload = {}
        if name is not MISSING:
            payload['name'] = name
        if description is not MISSING:
            payload['description'] = description
        if icon is not MISSING:
            payload['icon'] = resolve_image(icon)
        if banner is not MISSING:
            payload['banner'] = resolve_image(banner)
        if public is not MISSING:
            payload['public'] = public

        return await self.request('PATCH', f'/guilds/{guild_id}', json=payload)

    async def delete_guild(self, guild_id: int, *, password: str = MISSING) -> None:
        payload: DeleteGuildPayload | None = None if password is MISSING else {'password': password}
        await self.request('DELETE', f'/guilds/{guild_id}', json=payload)

    # Members

    async def get_members(self, guild_id: int) -> list[Member]:
        return await self.request('GET', f'/guilds/{guild_id}/members')

    async def get_member(self, guild_id: int, member_id: int) -> Member:
        return await self.request('GET', f'/guilds/{guild_id}/members/{member_id}')

    async def get_own_member(self, guild_id: int) -> Member:
        return await self.request('GET', f'/guilds/{guild_id}/members/me')

    async def edit_own_member(self, guild_id: int, *, nick: str | None = MISSING) -> Member:
        return await self.request('PATCH', f'/guilds/{guild_id}/members/me', json={'nick': nick})

    async def edit_member(
        self,
        guild_id: int,
        member_id: int,
        *,
        nick: str | None = MISSING,
        roles: list[int] = MISSING,
    ) -> Member:
        payload: EditMemberPayload = {}
        if nick is not MISSING:
            payload['nick'] = nick
        if roles is not MISSING:
            payload['roles'] = roles

        return await self.request('PATCH', f'/guilds/{guild_id}/members/{member_id}', json=payload)

    async def kick_member(self, guild_id: int, member_id: int) -> None:
        await self.request('DELETE', f'/guilds/{guild_id}/members/{member_id}')

    async def leave_guild(self, guild_id: int) -> None:
        await self.request('DELETE', f'/guilds/{guild_id}/members/me')

    async def close(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()
