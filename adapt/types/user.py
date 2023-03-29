from __future__ import annotations

from typing import Literal, TypedDict, TypeAlias

from . import Snowflake

__all__ = (
    'TokenRetrievalMethod',
    'LoginRequest',
    'LoginResponse',
)

TokenRetrievalMethod: TypeAlias = Literal['new', 'revoke', 'reuse']


class _LoginRequestRequired(TypedDict):
    email: str
    password: str


class LoginRequest(_LoginRequestRequired, total=False):
    method: TokenRetrievalMethod


class LoginResponse(TypedDict):
    id: Snowflake
    token: str
