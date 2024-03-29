from __future__ import annotations

from typing import Literal, TypedDict, TypeAlias

from . import Snowflake

__all__ = (
    'TokenRetrievalMethod',
    'RelationshipType',
    'LoginRequest',
    'LoginResponse',
    'CreateUserPayload',
    'CreateUserResponse',
    'User',
    'ClientUser',
    'Relationship',
)

TokenRetrievalMethod: TypeAlias = Literal['new', 'revoke', 'reuse']


class _LoginRequestRequired(TypedDict):
    email: str
    password: str


class LoginRequest(_LoginRequestRequired, total=False):
    method: TokenRetrievalMethod


class LoginResponse(TypedDict):
    user_id: Snowflake
    token: str


class _CreateUserPayloadRequired(TypedDict):
    username: str
    email: str
    password: str


class CreateUserPayload(_CreateUserPayloadRequired, total=False):
    display_name: str | None


class CreateUserResponse(TypedDict):
    id: Snowflake
    token: str


class _EditUserPayloadRequired(TypedDict):
    username: str


class EditUserPayload(_EditUserPayloadRequired, total=False):
    display_name: str | None
    avatar: str | None
    banner: str | None
    bio: str | None


class SendFriendRequestPayload(TypedDict):
    username: str


class User(TypedDict):
    id: Snowflake
    username: str
    display_name: str | None
    avatar: str | None
    banner: str | None
    bio: str | None
    flags: int


class ClientUser(User):
    email: str | None
    dm_privacy: int
    group_dm_privacy: int
    friend_request_privacy: int


RelationshipType: TypeAlias = Literal['friend', 'outgoing_request', 'incoming_request', 'blocked']


class Relationship(TypedDict):
    user: User
    type: RelationshipType
