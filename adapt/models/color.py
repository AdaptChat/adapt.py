from __future__ import annotations

from typing import Any

__all__ = ('Color',)


class Color:
    """Represents an integer color value.

    Attributes
    ----------
    value: :class:`int`
        The integer value of the color.
    """

    __slots__ = ('value',)

    def __init__(self, value: int) -> None:
        self.value = value

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} value={self.value}>'

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Color) and self.value == other.value

    def __int__(self) -> int:
        return self.value

    def __index__(self) -> int:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __bool__(self) -> bool:
        return bool(self.value)

    def __str__(self) -> str:
        return f'#{self.value:06x}'

    @property
    def r(self) -> int:
        """:class:`int`: The red component of the color."""
        return (self.value >> 16) & 0xff

    @property
    def g(self) -> int:
        """:class:`int`: The green component of the color."""
        return (self.value >> 8) & 0xff

    @property
    def b(self) -> int:
        """:class:`int`: The blue component of the color."""
        return self.value & 0xff

    @property
    def rgb(self) -> tuple[int, int, int]:
        """tuple[int, int, int]: A 3-tuple of the red, green, and blue components of the color."""
        return self.r, self.g, self.b

    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> Color:
        """Creates a :class:`Color` from RGB components.

        Parameters
        ----------
        r: :class:`int`
            The red component of the color.
        g: :class:`int`
            The green component of the color.
        b: :class:`int`
            The blue component of the color.

        Returns
        -------
        :class:`Color`
            The color created from the RGB components.
        """
        return cls((r << 16) | (g << 8) | b)
