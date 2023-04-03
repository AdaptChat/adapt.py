from __future__ import annotations

from typing import Literal, TypeAlias, TypedDict

from . import Snowflake, Timestamp
from .guild import Member
from .user import User

__all__ = (
    'EmbedType',
    'MessageEmbedFieldAlignment',
    'EmbedAuthor',
    'EmbedFooter',
    'EmbedField',
    'Embed',
    'Attachment',
    'MessageType',
    'Message',
    'CreateMessagePayload',
    'EditMessagePayload',
    'MessageHistoryQuery',
)

EmbedType: TypeAlias = Literal['rich', 'image', 'video', 'meta']
MessageEmbedFieldAlignment: TypeAlias = Literal['left', 'center', 'right', 'inline']


class _EmbedAuthorRequired(TypedDict):
    name: str


class EmbedAuthor(_EmbedAuthorRequired, total=False):
    url: str | None
    icon_url: str | None


class _EmbedFooterRequired(TypedDict):
    text: str


class EmbedFooter(_EmbedFooterRequired, total=False):
    icon_url: str | None


class _EmbedFieldRequired(TypedDict):
    name: str
    value: str


class EmbedField(_EmbedFieldRequired, total=False):
    align: MessageEmbedFieldAlignment


class _EmbedRequired(TypedDict):
    type: EmbedType


class Embed(_EmbedRequired, total=False):
    title: str | None
    description: str | None
    url: str | None
    timestamp: Timestamp | None
    color: int | None
    hue: int | None
    author: EmbedAuthor | None
    footer: EmbedFooter | None
    image: str | None
    thumbnail: str | None
    fields: list[EmbedField] | None


class _AttachmentRequired(TypedDict):
    id: Snowflake
    filename: str
    size: int
    url: str


class Attachment(_AttachmentRequired, total=False):
    description: str | None


MessageType: TypeAlias = Literal['default', 'join', 'leave', 'pin']


class _MessageRequired(TypedDict):
    id: Snowflake
    revision_id: Snowflake | None
    channel_id: Snowflake
    author_id: Snowflake | None
    author: Member | User | None
    type: MessageType
    content: str | None
    embeds: list[Embed]
    attachments: list[Attachment]
    flags: int
    starts: int


class Message(_MessageRequired, total=False):
    # Join, Leave
    user_id: Snowflake
    # Pin
    pinned_message_id: Snowflake
    pinned_by: Snowflake


class CreateMessagePayload(TypedDict, total=False):
    content: str | None
    embeds: list[Embed] | None
    nonce: str | None


class EditMessagePayload(TypedDict, total=False):
    content: str | None
    embeds: list[Embed] | None


class MessageHistoryQuery(TypedDict, total=False):
    before: int
    after: int
    limit: int
    user_id: Snowflake
    oldest_first: bool
