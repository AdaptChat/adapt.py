from base64 import b64encode
from inspect import isawaitable
from typing import (
    Any,
    Awaitable,
    Callable,
    Optional,
    ParamSpec,
    TypeVar,
    Union,
    overload,
)

__all__ = (
    'maybe_coro',
    '_try_int',
    '_get_mimetype',
    '_bytes_to_image_data',
)

T = TypeVar('T', bound='Ratelimiter')
P = ParamSpec('P')
R = TypeVar('R')


async def maybe_coro(func: Callable[P, Awaitable[R] | R], *args: P.args, **kwargs: P.kwargs) -> Awaitable[R]:
    res = func(*args, **kwargs)
    if isawaitable(res):
        return await res

    return res


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


@overload
def _try_int(value: int, /) -> int:
    ...


@overload
def _try_int(value: str, /) -> Optional[int]:
    ...


@overload
def _try_int(value: None, /) -> None:
    ...


def _try_int(value, /):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None
