from __future__ import annotations

from datetime import datetime
from typing import Any, TYPE_CHECKING

from .color import Color
from .enums import EmbedFieldAlignment, EmbedType

if TYPE_CHECKING:
    from typing import Literal, TypeAlias

    from ..types.message import (
        Embed as RawEmbed,
        EmbedAuthor as RawEmbedAuthor,
        EmbedField as RawEmbedField,
        EmbedFooter as RawEmbedFooter,
    )

    FieldAlignmentString: TypeAlias = Literal['left', 'center', 'right', 'inline']
    FieldAlignment: TypeAlias = FieldAlignmentString | EmbedFieldAlignment

__all__ = ('Embed',)


class EmbedAuthor:
    """Represents the author of an embed.

    Attributes
    ----------
    name: :class:`str`
        The name of the author.
    url: :class:`str` | None
        The URL of the author, if any.
    icon_url: :class:`str` | None
        The URL of the icon of the author, if any.
    """

    __slots__ = ('name', 'url', 'icon_url')

    def __init__(self, name: str, *, url: str | None = None, icon_url: str | None = None) -> None:
        self.name = name
        self.url = url
        self.icon_url = icon_url

    def to_dict(self) -> RawEmbedAuthor:
        return {
            'name': self.name,
            'url': self.url,
            'icon_url': self.icon_url
        }


class EmbedFooter:
    """Represents the footer of an embed.

    Attributes
    ----------
    text: :class:`str`
        The text of the footer.
    icon_url: :class:`str` | None
        The URL of the icon of the footer, if any.
    """

    __slots__ = ('text', 'icon_url')

    def __init__(self, text: str, *, icon_url: str | None = None) -> None:
        self.text = text
        self.icon_url = icon_url

    def to_dict(self) -> RawEmbedFooter:
        return {
            'text': self.text,
            'icon_url': self.icon_url
        }


class EmbedField:
    """Represents a field of an embed.

    Attributes
    ----------
    name: :class:`str`
        The name of the field.
    value: :class:`str`
        The value of the field.
    align: :class:`.EmbedFieldAlignment` | :class:`str`
        The alignment of the field.
    """

    __slots__ = ('name', 'value', 'align')

    def __init__(self, name: str, value: str, *, align: FieldAlignment = EmbedFieldAlignment.inline) -> None:
        self.name = name
        self.value = value
        self.align = EmbedFieldAlignment(align)

    def to_dict(self) -> RawEmbedField:
        return {
            'name': self.name,
            'value': self.value,
            'align': self.align.value,
        }


class Embed:
    """Represents a special card shown in the UI for various purposes, embedding extra information to the user in a more
    visually appealing way. These are known as embeds and are used in messages.

    .. note::
       You may only create :attr:`~.EmbedType.rich` embeds.

    Attributes
    ----------
    type: :class:`.EmbedType`
        The type of the embed.
    title: :class:`str` | None
        The title of the embed, if any. Can be up to 256 bytes in length.
    description: :class:`str` | None
        The description of the embed, if any. Can be up to 4096 bytes in length.
    url: :class:`str` | None
        The URL of the embed, if any. This must be a well-formed URL.
        This is typically displayed as a link masked by the embed's :attr:`~.Embed.title`.
    timestamp: :class:`datetime.datetime` | None
        The timestamp of the embed, if any.
    color: :class:`.Color` | None
        The color of the embed, if any. This is shown as a stripe on the left side of the embed.
    hue: :class:`int` | None
        The hue of the embed, in percent, if any. This value must fall between ``0`` and ``100`` (inclusive).
    author: :class:`.EmbedAuthor` | None
        The author of the embed, if any. This is shown at the top of the embed.
    footer: :class:`.EmbedFooter` | None
        The footer of the embed, if any. This is shown at the bottom of the embed.
    image: :class:`str` | None
        The URL of the image of the embed, if any. This is the big image shown below the description and embed fields.
    thumbnail: :class:`str` | None
        The URL of the thumbnail of the embed, if any. This is the small image shown in the top-right corner of the
        embed.
    fields: list[:class:`.EmbedField`]
        The fields of the embed.
    """

    __slots__ = (
        'type',
        'title',
        'description',
        'url',
        'timestamp',
        'color',
        'hue',
        'author',
        'footer',
        'image',
        'thumbnail',
        'fields',
    )

    def __init__(
        self,
        *,
        title: Any = None,
        description: Any = None,
        url: str | None = None,
        timestamp: datetime | None = None,
        color: Color | None = None,
        hue: int | None = None,
        image: str | None = None,
        thumbnail: str | None = None,
    ) -> None:
        self.type = EmbedType.rich
        self.title = str(title) if title is not None else None
        self.description = str(description) if description is not None else None
        self.url = url
        self.timestamp = timestamp
        self.color = color
        self.hue = hue
        self.author: EmbedAuthor | None = None
        self.footer: EmbedFooter | None = None
        self.image = image
        self.thumbnail = thumbnail
        self.fields: list[EmbedField] = []

    def add_field(self, name: str, value: str, *, align: FieldAlignment = EmbedFieldAlignment.inline) -> Embed:
        """Adds a field to the embed.

        Parameters
        ----------
        name: :class:`str`
            The name of the field.
        value: :class:`str`
            The value of the field.
        align: :class:`.EmbedFieldAlignment` | :class:`str`
            The alignment of the field.
        """
        self.fields.append(EmbedField(name, value, align=align))
        return self

    def set_author(self, name: str, *, url: str | None = None, icon_url: str | None = None) -> Embed:
        """Sets the author of the embed.

        Parameters
        ----------
        name: :class:`str`
            The name of the author.
        url: :class:`str` | None
            The URL of the author, if any.
        icon_url: :class:`str` | None
            The URL of the icon of the author, if any.
        """
        self.author = EmbedAuthor(name, url=url, icon_url=icon_url)
        return self

    def set_footer(self, text: str, *, icon_url: str | None = None) -> Embed:
        """Sets the footer of the embed.

        Parameters
        ----------
        text: :class:`str`
            The text of the footer.
        icon_url: :class:`str` | None
            The URL of the icon of the footer, if any.
        """
        self.footer = EmbedFooter(text, icon_url=icon_url)
        return self

    @classmethod
    def from_dict(cls, data: RawEmbed) -> Embed:
        embed = cls(
            title=data.get('title'),
            description=data.get('description'),
            url=data.get('url'),
            timestamp=data.get('timestamp'),
            color=Color(data.get('color')) if data.get('color') is not None else None,
            hue=data.get('hue'),
            image=data.get('image'),
            thumbnail=data.get('thumbnail'),
        )
        embed.type = EmbedType(data['type'])

        if author := data.get('author'):
            embed.set_author(author['name'], url=author.get('url'), icon_url=author.get('icon_url'))

        if footer := data.get('footer'):
            embed.set_footer(footer['text'], icon_url=footer.get('icon_url'))

        for field in data.get('fields', []):
            embed.add_field(field['name'], field['value'], align=EmbedFieldAlignment(field.get('align', 'inline')))

        return embed

    def to_dict(self) -> RawEmbed:
        """:class:`dict`: The JSON representation of the embed."""
        return {
            'type': self.type.value,
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'timestamp': self.timestamp,
            'color': self.color.value if self.color is not None else None,
            'hue': self.hue,
            'author': self.author.to_dict() if self.author is not None else None,
            'footer': self.footer.to_dict() if self.footer is not None else None,
            'image': self.image,
            'thumbnail': self.thumbnail,
            'fields': [field.to_dict() for field in self.fields],
        }
