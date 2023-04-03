from __future__ import annotations

from typing import NamedTuple, TYPE_CHECKING

from .util import IS_DOCUMENTING

if TYPE_CHECKING:
    from typing import Self


class AdaptServer(NamedTuple):
    """Represents connection URLs or locations of the Adapt API server.

    Parameters
    ----------
    api: :class:`str`
        The URL of the HTTP REST API. (e.g. https://api.adapt.chat)
    harmony: :class:`str`
        The URL of the websocket API. (e.g. wss://harmony.adapt.chat)
    convey: :class:`str`
        The URL of the file upload and CDN API. (e.g. https://convey.adapt.chat)
    """
    api: str
    harmony: str
    convey: str

    @classmethod
    def production(cls) -> Self:
        """A :class:`AdaptServer` instance representing the production Adapt API server (`adapt.chat`).

        This is the default server used by the library.
        """
        return cls(
            api='https://api.adapt.chat',
            harmony='wss://harmony.adapt.chat',
            convey='https://convey.adapt.chat',
        )

    @classmethod
    def local(cls) -> Self:
        """A :class:`AdaptServer` instance representing a local Adapt API server with default ports extracted from
        Adapt's source code.

        This is useful for testing.
        """
        return cls(
            api='http://localhost:8077',
            harmony='ws://localhost:8076',
            convey='http://localhost:8078',
        )

    def copy_with(self, *, api: str | None = None, harmony: str | None = None, convey: str | None = None) -> Self:
        """Create a copy of this :class:`AdaptServer` with the specified parameters replaced.

        Parameters
        ----------
        api: :class:`str`
            The URL of the HTTP REST API. (e.g. https://api.adapt.chat)
        harmony: :class:`str`
            The URL of the websocket API. (e.g. wss://harmony.adapt.chat)
        convey: :class:`str`
            The URL of the file upload and CDN API. (e.g. https://convey.adapt.chat)
        """
        return AdaptServer(
            api=api or self.api,
            harmony=harmony or self.harmony,
            convey=convey or self.convey,
        )

    if IS_DOCUMENTING:
        def __repr__(self) -> str:
            return 'AdaptServer.production()'
