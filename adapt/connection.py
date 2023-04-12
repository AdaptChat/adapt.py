from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from .models.channel import DMChannel
from .models.enums import RelationshipType, Status
from .models.guild import Guild
from .models.message import Message
from .models.ready import ReadyEvent
from .models.user import ClientUser, Relationship, User
from .server import AdaptServer

if TYPE_CHECKING:
    from typing import Any

    from .http import HTTPClient
    from .types.channel import DMChannel as RawDMChannel
    from .types.guild import Guild as RawGuild
    from .types.user import User as RawUser, Relationship as RawRelationship
    from .types.ws import (
        InboundMessage,
        ReadyEvent as RawReadyEvent,
        UserUpdateEvent,
        GuildCreateEvent,
        GuildUpdateEvent,
        MessageCreateEvent,
    )
    from .websocket import Dispatcher

__all__ = ('Connection',)


class Connection:
    """Represents a connection state to the Adapt API."""

    __slots__ = (
        'http',
        'server',
        'loop',
        'user',
        'dispatch',
        '_connect_status',
        '_is_ready',
        '_token',
        '_max_message_count',
        '_users',
        '_relationships',
        '_dm_channels',
        '_guilds',
    )

    if TYPE_CHECKING:
        _users: dict[int, User]
        _relationships: dict[int, Relationship]
        _dm_channels: dict[int, DMChannel]  # TODO DMChannel
        _guilds: dict[int, Guild]

    def __init__(
        self,
        *,
        http: HTTPClient,
        server: AdaptServer = AdaptServer.production(),
        loop: asyncio.AbstractEventLoop | None = None,
        dispatch: Dispatcher,
        max_message_count: int = 1000,
        status: Status = Status.online,
    ) -> None:
        self.http = http
        self.server = server
        self.loop = loop or http.loop
        self.user: ClientUser | None = None
        self.dispatch = dispatch

        self._connect_status: Status = status
        self._is_ready: asyncio.Future[ReadyEvent] = loop.create_future()
        self._token: str | None = None
        self._max_message_count = max_message_count

        self._users = {}
        self._relationships = {}
        self._dm_channels = {}
        self._guilds = {}

    def invalidate_caches(self) -> None:
        """Clears the internal caches of the connection."""
        self._users.clear()
        self._relationships.clear()
        self._dm_channels.clear()
        self._guilds.clear()

    def get_user(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    def add_user(self, user: User) -> User:
        self._users[user.id] = user
        return user

    def add_raw_user(self, data: RawUser) -> User:
        if user := self.get_user(data['id']):
            user._update(data)
            return user

        return self.add_user(User(connection=self, data=data))

    def get_relationship(self, user_id: int) -> Relationship | None:
        return self._relationships.get(user_id)

    def update_relationship(self, *, user_id: int, type: RelationshipType) -> Relationship:
        if relationship := self.get_relationship(user_id):
            relationship._type = type
            return relationship

        self._relationships[user_id] = new = Relationship(connection=self, user_id=user_id, type=type)
        return new

    def update_raw_relationship(self, data: RawRelationship) -> Relationship:
        self.add_raw_user(user := data['user'])
        return self.update_relationship(user_id=user['id'], type=RelationshipType(data['type']))

    def get_guild(self, guild_id: int) -> Guild | None:
        return self._guilds.get(guild_id)

    def add_guild(self, guild: Guild) -> Guild:
        self._guilds[guild.id] = guild
        return guild

    def add_raw_guild(self, data: RawGuild) -> Guild:
        if guild := self.get_guild(data['id']):
            guild._update(data)
            return guild

        return self.add_guild(Guild(connection=self, data=data))

    def get_dm_channel(self, channel_id: int) -> DMChannel | None:
        return self._dm_channels.get(channel_id)

    def add_dm_channel(self, channel: DMChannel) -> DMChannel:
        self._dm_channels[channel.id] = channel
        return channel

    def add_raw_dm_channel(self, data: RawDMChannel) -> DMChannel:
        if channel := self.get_dm_channel(data['id']):
            channel._update(data)
            return channel

        return self.add_dm_channel(DMChannel(connection=self, data=data))

    def process_event(self, data: InboundMessage) -> None:
        event: str = data['event']
        data: dict[str, Any] = data.get('data')

        if handler := getattr(self, '_handle_' + event, None):
            handler(data)

    def _handle_ready(self, data: RawReadyEvent) -> None:
        ready = ReadyEvent(connection=self, data=data)

        if not self._is_ready.done():
            self._is_ready.set_result(ready)

        self.dispatch('ready', ready)

    def _handle_user_update(self, data: UserUpdateEvent) -> None:
        before = User(connection=self, data=data['before'])
        user = self.add_raw_user(data['after'])

        self.dispatch('user_update', before, user)

    def _handle_guild_create(self, data: GuildCreateEvent) -> None:
        guild = self.add_raw_guild(data['guild'])
        self.dispatch('guild_create', guild)  # TODO: dispatch nonce

    def _handle_guild_update(self, data: GuildUpdateEvent) -> None:
        before = Guild(connection=self, data=data['before'])
        if guild := self._guilds.get(before.id):
            guild._update(data['after'])

        self.dispatch('guild_update', before, guild)

    def _handle_message_create(self, data: MessageCreateEvent) -> None:
        message = data['message']
        if guild_id := message['author'].get('guild_id'):
            guild = self.get_guild(guild_id)
            channel = guild.get_channel(message['channel_id'])
        else:
            channel = self.get_dm_channel(message['channel_id'])

        message = Message(channel=channel, data=message)
        self.dispatch('message', message)  # TODO: dispatch nonce
