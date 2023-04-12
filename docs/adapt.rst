Adapt.py API Reference
======================

Client and Events
-----------------

Client
~~~~~~

.. autoclass:: adapt.Client
    :members:

Server
~~~~~~

.. autoclass:: adapt.AdaptServer
    :members:

Events
~~~~~~

.. autoclass:: adapt.client.EventDispatcher
    :members:

Event Utilities
~~~~~~~~~~~~~~~

.. autofunction:: adapt.once

.. autoclass:: adapt.ReadyEvent
    :members:

Models
------

Object
~~~~~~

.. autoclass:: adapt.Object
    :members:
    :inherited-members:

User
~~~~

.. autoclass:: adapt.User()
    :members:
    :inherited-members:

ClientUser
~~~~~~~~~~

.. autoclass:: adapt.ClientUser()
    :members:
    :inherited-members:

PartialUser
~~~~~~~~~~~

.. autoclass:: adapt.PartialUser()
    :members:
    :inherited-members:

Relationship
~~~~~~~~~~~~

.. autoclass:: adapt.Relationship()
    :members:
    :inherited-members:

Guild
~~~~~

.. autoclass:: adapt.Guild()
    :members:
    :inherited-members:

PartialGuild
~~~~~~~~~~~~

.. autoclass:: adapt.PartialGuild()
    :members:
    :inherited-members:

Member
~~~~~~

.. autoclass:: adapt.Member()
    :members:
    :inherited-members:

PartialMember
~~~~~~~~~~~~~

.. autoclass:: adapt.PartialMember()
    :members:
    :inherited-members:

PartialMessageable
~~~~~~~~~~~~~~~~~~

.. autoclass:: adapt.PartialMessageable()
    :members:
    :inherited-members:

TextChannel
~~~~~~~~~~~

.. autoclass:: adapt.TextChannel()
    :members:
    :inherited-members:

AnnouncementChannel
~~~~~~~~~~~~~~~~~~~

.. autoclass:: adapt.AnnouncementChannel()
    :members:
    :inherited-members:

DMChannel
~~~~~~~~~

.. autoclass:: adapt.DMChannel()
    :members:
    :inherited-members:

Message
~~~~~~~

.. autoclass:: adapt.Message()
    :members:
    :inherited-members:

PartialMessage
~~~~~~~~~~~~~~

.. autoclass:: adapt.PartialMessage
    :members:
    :inherited-members:

Asset
~~~~~

.. autoclass:: adapt.Asset()
    :members:
    :inherited-members:

Base Classes
------------

Messageable
~~~~~~~~~~~

.. autoclass:: adapt.Messageable()
    :members:

GuildChannel
~~~~~~~~~~~~

.. autoclass:: adapt.GuildChannel()
    :members:
    :inherited-members:

PrivateChannel
~~~~~~~~~~~~~~

.. autoclass:: adapt.PrivateChannel()
    :members:
    :inherited-members:

Enums
-----

Standard Enums
~~~~~~~~~~~~~~

.. autoclass:: adapt.ModelType()
    :members:

.. autoclass:: adapt.Status()
    :members:

.. autoclass:: adapt.RelationshipType()
    :members:

.. autoclass:: adapt.ChannelType()
    :members:

.. autoclass:: adapt.MessageType()
    :members:

Bitflag Enums
~~~~~~~~~~~~~

.. autoclass:: adapt.Bitflags
    :members:

.. autoclass:: adapt.UserFlags
    :members:

.. autoclass:: adapt.PrivacyConfiguration
    :members:

.. autoclass:: adapt.GuildFlags
    :members:

.. autoclass:: adapt.MessageFlags
    :members:

.. autoclass:: adapt.RoleFlags
    :members:

.. autoclass:: adapt.Permissions
    :members:

Utility Functions
-----------------

.. automodule:: adapt.util
    :members:
