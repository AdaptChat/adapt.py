from __future__ import annotations

from base64 import b64encode, urlsafe_b64decode
from datetime import datetime
from inspect import isawaitable
from typing import (
    Any,
    Awaitable,
    Callable,
    Final,
    ParamSpec,
    TypeVar,
)

from .models.enums import ModelType

__all__ = (
    'ADAPT_EPOCH_MILLIS',
    'Ratelimiter',
    'maybe_coro',
    'extract_user_id_from_token',
    'snowflake_model_type',
    'snowflake_time',
)

T = TypeVar('T', bound='Ratelimiter')
P = ParamSpec('P')
R = TypeVar('R')

ADAPT_EPOCH_MILLIS: Final[int] = 1_671_926_400_000


class _Missing:
    __slots__ = ()

    def __eq__(self, other: Any) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __hash__(self) -> int:
        return 0

    def __repr__(self) -> str:
        return '...'


MISSING: Any = _Missing()


# FIXME: Replace when Ratelimiter exists
class Ratelimiter:
    ...


async def maybe_coro(func: Callable[P, Awaitable[R] | R], /, *args: P.args, **kwargs: P.kwargs) -> R:
    res = func(*args, **kwargs)
    if isawaitable(res):
        return await res

    return res  # type: ignore


def _get_mimetype(data: bytes) -> str:
    if data.startswith(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'):
        return 'image/png'
    elif data[0:3] == b'\xff\xd8\xff' or data[6:10] in (b'JFIF', b'Exif'):
        return 'image/jpeg'
    elif data.startswith((b'\x47\x49\x46\x38\x37\x61', b'\x47\x49\x46\x38\x39\x61')):
        return 'image/gif'
    elif data.startswith(b'RIFF') and data[8:12] == b'WEBP':
        return 'image/webp'

    raise ValueError('unsupported image format')


def _bytes_to_image_data(data: bytes) -> str:
    mimetype = _get_mimetype(data)
    result = b64encode(data).decode('ascii')
    return f'data:{mimetype};base64,{result}'


def extract_user_id_from_token(token: str, /) -> int:
    """Extracts the user ID associated with the given authentication token.

    Parameters
    ----------
    token: :class:`str`
        The token to parse.

    Returns
    -------
    :class:`int`
        The snowflake ID of the associated user.

    Raises
    ------
    ValueError
        Received a malformed token.
    """
    return int(urlsafe_b64decode(token.split('.', maxsplit=1)[0]))


def snowflake_time(snowflake: int, /) -> datetime:
    """Converts an Adapt snowflake to a datetime object.

    Parameters
    ----------
    snowflake: :class:`int`
        The snowflake to convert.

    Returns
    -------
    :class:`datetime.datetime`
        The datetime object representing the snowflake's creation time.
    """
    return datetime.utcfromtimestamp(((snowflake >> 18) + ADAPT_EPOCH_MILLIS) / 1000)


def snowflake_model_type(snowflake: int, /) -> ModelType:
    """Extracts the model type of the given Adapt snowflake.

    Parameters
    ----------
    snowflake: :class:`int`
        The snowflake to extract the model type from.

    Returns
    -------
    :class:`ModelType`
        The model type associated with the snowflake.
    """
    return ModelType((snowflake >> 13) & 0b11111)
