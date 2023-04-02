from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .object import AdaptObject
from ..util import MISSING

if TYPE_CHECKING:
    from ..connection import Connection


class TextBasedChannel(ABC):
    """Represents a channel that can be a medium for text-based communication."""

    __slots__ = ('_connection',)

    _connection: Connection

    @abstractmethod
    async def _get_channel_id(self) -> int:
        raise NotImplementedError

    async def send(self, content: str = MISSING, *, nonce: str = MISSING) -> Message:
        """|coro|

        Sends a message to the channel.

        Parameters
        ----------
        content: :class:`str`
            The content of the message to send.
        nonce: :class:`str`
            An optional nonce for integrity. When this message is received through the websocket, the nonce will be
            included in the message payload. This can be used to verify that the essage was sent successfully.

        Returns
        -------
        :class:`.Message`
            The message that was sent.
        """
        # todo!()
