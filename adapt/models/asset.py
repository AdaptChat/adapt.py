from __future__ import annotations

from io import BufferedIOBase
from typing import overload, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Literal, Self

    from ..connection import Connection
    from ..util import IOSource

__all__ = ('Asset',)


class AssetLike:
    """Represents any CDN entry from convey, Adapt's CDN server."""

    __slots__ = ('_connection', 'url', '_cached')

    def __init__(self, *, connection: Connection | None, url: str) -> None:
        self._connection = connection
        self.url = url
        self._cached: bytes | None = None

    async def read(self, *, cache: bool = True) -> bytes:
        """|coro|

        Downloads the asset's contents into raw bytes. This cannot be used if the asset is stateless.

        .. note::
            For assets that are cached, the cache is held on the **asset object** and not the connection. This means
            that two different asset objects may not share the same cache.

        Parameters
        ----------
        cache: :class:`bool`
            Whether to cache the asset. Defaults to ``True``. If this is enabled, future calls to ``read``
            will return the cached bytes instead of downloading the asset again.

        Returns
        -------
        bytes
            The raw bytes of the asset.

        Raises
        ------
        TypeError
            If the asset is stateless.
        """
        if not self._connection:
            raise TypeError('Cannot read stateless asset')

        if cache and self._cached is not None:
            return self._cached

        async with self._connection.http.session.get(self.url) as response:
            data = await response.read()
            if cache:
                self._cached = data
            return data

    async def save(self, fp: IOSource, *, cache: bool = True, seek_begin: bool = True) -> int:
        """|coro|

        Downloads the asset's contents and saves it to a file. This cannot be used if the asset is stateless.

        .. note::
            For assets that are cached, the cache is held on the **asset object** and not the connection. This means
            that two different asset objects may not share the same cache.

        Parameters
        ----------
        fp: :class:`str`, :class:`pathlib.Path`, or file-like object
            The file path or file-like object to save the asset to.
        cache: :class:`bool`
            Whether to cache the asset. Defaults to ``True``. If this is enabled, future calls to ``save``
            will not download the asset again.
        seek_begin: :class:`bool`
            Whether to seek to the beginning of the file after writing. Defaults to ``True``.

        Returns
        -------
        int
            The number of bytes written to the file.

        Raises
        ------
        :exc:`TypeError`
            - If the file-like object does not support the ``write`` method.
            - If the asset is stateless.
        """
        data = await self.read(cache=cache)

        if isinstance(fp, BufferedIOBase):
            written = fp.write(data)
            if seek_begin:
                fp.seek(0)
            return written

        with open(fp, 'wb') as f:
            return f.write(data)

    def __bytes__(self) -> bytes:
        return self._cached or b''

    def __str__(self) -> str:
        return self.url

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} route={self.url!r}>'

    @overload
    def __eq__(self, other: Self) -> bool:
        ...

    @overload
    def __eq__(self, other: Any) -> Literal[False]:
        ...

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.url == other.url

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.url)


class Asset(AssetLike):
    """Represents an asset from Adapt's CDN, convey.

    Attributes
    ----------
    url: :class:`str`
        The URL of the asset.
    """
