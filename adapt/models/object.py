from __future__ import annotations

from abc import ABC
from collections.abc import Hashable
from datetime import datetime
from typing import Protocol, TYPE_CHECKING

from .enums import ModelType
from ..util import snowflake_model_type, snowflake_time

if TYPE_CHECKING:
    from typing import Self

__all__ = (
    'BaseObject',
    'AdaptObject',
    'Object',
)


class ObjectLike(Protocol):
    __slots__ = ()

    @property
    def id(self) -> int:
        ...

    def __eq__(self, other: Self) -> bool:
        ...

    def __hash__(self) -> int:
        ...


class BaseObject(Hashable, ABC):
    """An abstract base class for all objects that have an ID."""

    __slots__ = ('_id',)
    _id: int

    @property
    def id(self) -> int:
        """The ID of the object."""
        raise NotImplementedError

    def __eq__(self, other: Self) -> bool:
        return isinstance(other, self.__class__) and self.id == other.id

    def __ne__(self, other: Self) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id}>'


class AdaptObject(BaseObject, ABC):
    """The base class that all Adapt objects inherit from."""

    __slots__ = ()

    @property
    def id(self) -> int:
        """The ID of the object."""
        return self._id

    @property
    def created_at(self) -> datetime:
        """The time the object was created."""
        return snowflake_time(self.id)


class Object(AdaptObject):
    """A generic Adapt object that has an ID.

    Parameters
    ----------
    id: :class:`int`
        The ID of the object.
    model_type: :class:`ModelType`
        The type of model the object is. If not provided, the model type will be calculated from the ID.
        If it is provided, the ID will be **modified** to match the provided model type.
    """

    __slots__ = ('_id',)

    def __init__(self, id: int, *, model_type: ModelType | None = None) -> None:
        self._id = id

        if model_type is not None:
            self.model_type = model_type

    @property
    def model_type(self) -> ModelType:
        """The type of model the object is."""
        return snowflake_model_type(self.id)

    @model_type.setter
    def model_type(self, value: ModelType) -> None:
        self._id = (self._id & ~(0b11111 << 13)) | (value.value << 13)

    def __repr__(self) -> str:
        return f'<Object id={self.id} model_type={self.model_type}>'
