from __future__ import annotations

from typing import TYPE_CHECKING

from .object import AdaptObject

if TYPE_CHECKING:
    from ..types.guild import Member as RawMember

__all__ = ('Member',)


class Member(AdaptObject):
    """"""
