from __future__ import annotations

import warnings
from base64 import b64encode, urlsafe_b64decode
from datetime import datetime
from functools import wraps
from inspect import isawaitable
from io import BufferedIOBase
from os import getenv
from typing import (
    Any,
    Awaitable,
    Callable,
    Final,
    ParamSpec,
    TypeVar,
    TYPE_CHECKING,
)

from .models.enums import ModelType

if TYPE_CHECKING:
    from os import PathLike
    from typing import Iterable, Literal, TypeAlias

    IOSource: TypeAlias = str | bytes | PathLike[Any] | BufferedIOBase
    IS_DOCUMENTING: Literal[False] = False
else:
    IS_DOCUMENTING: bool = getenv('READTHEDOCS', False)

__all__ = (
    'ADAPT_EPOCH_MILLIS',
    'Ratelimiter',
    'maybe_coro',
    'extract_user_id_from_token',
    'snowflake_model_type',
    'snowflake_time',
    'find',
)

T = TypeVar('T')
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


def _bytes_to_image_data(data: bytes, /) -> str:
    mimetype = _get_mimetype(data)
    result = b64encode(data).decode('ascii')
    return f'data:{mimetype};base64,{result}'


def resolve_image(src: IOSource, /) -> str:
    if isinstance(src, bytes):
        data = src
    elif isinstance(src, BufferedIOBase):
        data = src.read()
    else:
        with open(src, 'rb') as f:
            data = f.read()
    return _bytes_to_image_data(data)


def deprecated(
    *,
    since: str = MISSING,
    removed_in: str = MISSING,
    use: str,
    reason: str = MISSING,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            warnings.simplefilter('always', DeprecationWarning)

            fmt = (
                '{0.__qualname__} is deprecated'
                if since is MISSING
                else '{0.__qualname__} was deprecated since v{since}'
            )
            if removed_in is not MISSING:
                fmt += ' and will be removed in v{removed_in}'

            fmt += '. Use {use} instead.'
            if reason is not MISSING:
                fmt += ' {reason}'

            message = fmt.format(func, since=since, removed_in=removed_in, use=use, reason=reason)
            warnings.warn(message, DeprecationWarning, stacklevel=3)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def parse_datetime(iso: str, /) -> datetime:
    # fromisoformat does not support the Z timezone with fractional seconds
    return datetime.fromisoformat(iso.replace('Z', '+00:00'))


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


def find(iterable: Iterable[T], predicate: Callable[[T], bool]) -> T | None:
    """Finds the first element in an iterable that satisfies the given predicate.

    Parameters
    ----------
    iterable: Iterable[T]
        The iterable to search through.
    predicate: (item: T) -> :class:`bool`
        The predicate to use to find the element.

    Returns
    -------
    T | None
        The first element that satisfies the predicate, or ``None`` if no such element is found.
    """
    for item in iterable:
        if predicate(item):
            return item
    return None
